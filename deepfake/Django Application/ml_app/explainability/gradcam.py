"""
Grad-CAM Explainability Module

Provides visual explanations of WHY the model thinks a frame is fake.
Uses gradient-weighted class activation mapping on ResNeXt CNN feature maps.

IMPORTANT: This module does NOT modify the model or inference logic.
It only hooks into existing forward passes to extract gradient information.
"""

import torch
import torch.nn.functional as F
import numpy as np
import cv2
from typing import Tuple, Optional, List, Dict, Any
import os


class GradCAMExplainer:
    """
    Grad-CAM explainer for ResNeXt + LSTM deepfake detection model.
    
    Hooks into the final convolutional block of ResNeXt to generate
    visual explanations without modifying the model.
    """
    
    def __init__(self, model: torch.nn.Module, target_layer_name: str = 'model'):
        """
        Initialize Grad-CAM explainer.
        
        Args:
            model: The deepfake detection model (ResNeXt + LSTM)
            target_layer_name: Name of the layer to hook (default: 'model' which is ResNeXt backbone)
        """
        self.model = model
        self.target_layer_name = target_layer_name
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self.hooks: List = []
        
        self._register_hooks()
    
    def _register_hooks(self) -> None:
        """Register forward and backward hooks on the target layer."""
        # Get the target layer (ResNeXt backbone - final conv block)
        target_layer = None
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                target_layer = module
                break
        
        if target_layer is None:
            # Fallback: use the model's CNN backbone directly
            target_layer = self.model.model
        
        # Register forward hook to capture activations
        forward_hook = target_layer.register_forward_hook(self._forward_hook)
        self.hooks.append(forward_hook)
        
        # Register backward hook to capture gradients
        backward_hook = target_layer.register_full_backward_hook(self._backward_hook)
        self.hooks.append(backward_hook)
    
    def _forward_hook(self, module: torch.nn.Module, input: Tuple, output: torch.Tensor) -> None:
        """Capture activations during forward pass."""
        self.activations = output.detach()
    
    def _backward_hook(self, module: torch.nn.Module, grad_input: Tuple, grad_output: Tuple) -> None:
        """Capture gradients during backward pass."""
        self.gradients = grad_output[0].detach()
    
    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
        frame_idx: int = -1
    ) -> Tuple[np.ndarray, int, float]:
        """
        Generate Grad-CAM heatmap for a given input.
        
        Args:
            input_tensor: Input tensor of shape (batch, seq_len, channels, height, width)
            target_class: Target class for CAM (None = use predicted class)
            frame_idx: Which frame in sequence to explain (-1 = last frame)
        
        Returns:
            Tuple of (heatmap as numpy array, predicted class, confidence)
        """
        self.model.eval()
        
        # Enable gradients for this computation
        input_tensor.requires_grad_(True)
        
        # Forward pass
        fmap, logits = self.model(input_tensor)
        
        # Apply softmax to get probabilities
        probs = F.softmax(logits, dim=1)
        
        # Get prediction
        pred_class = logits.argmax(dim=1).item()
        confidence = probs[0, pred_class].item()
        
        # Use predicted class if target not specified
        if target_class is None:
            target_class = pred_class
        
        # Get the score for target class
        score = logits[0, target_class]
        
        # Backward pass
        self.model.zero_grad()
        score.backward(retain_graph=True)
        
        # Get gradients and activations
        gradients = self.gradients
        activations = self.activations
        
        if gradients is None or activations is None:
            raise RuntimeError("Failed to capture gradients or activations. Check hook registration.")
        
        # Calculate frame-specific CAM
        batch_size, seq_length = input_tensor.shape[:2]
        
        # Reshape activations/gradients for frame-wise processing
        # Shape: (batch * seq_len, channels, h, w)
        num_frames = batch_size * seq_length
        
        # Select frame to explain
        if frame_idx == -1:
            frame_idx = seq_length - 1
        
        frame_activation = activations[frame_idx]  # (channels, h, w)
        frame_gradient = gradients[frame_idx]  # (channels, h, w)
        
        # Global average pooling of gradients to get weights
        weights = torch.mean(frame_gradient, dim=(1, 2))  # (channels,)
        
        # Weighted combination of activation maps
        cam = torch.zeros(frame_activation.shape[1:], dtype=torch.float32, device=frame_activation.device)
        for i, w in enumerate(weights):
            cam += w * frame_activation[i]
        
        # Apply ReLU (only positive contributions)
        cam = F.relu(cam)
        
        # Normalize
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()
        
        # Convert to numpy
        cam_np = cam.cpu().numpy()
        
        return cam_np, pred_class, confidence
    
    def generate_heatmap_overlay(
        self,
        input_tensor: torch.Tensor,
        original_frame: np.ndarray,
        target_class: Optional[int] = None,
        frame_idx: int = -1,
        colormap: int = cv2.COLORMAP_JET,
        alpha: float = 0.5
    ) -> Tuple[np.ndarray, np.ndarray, int, float]:
        """
        Generate Grad-CAM heatmap and overlay on original frame.
        
        Args:
            input_tensor: Model input tensor
            original_frame: Original frame as numpy array (H, W, C) in BGR or RGB
            target_class: Target class for CAM
            frame_idx: Frame index in sequence
            colormap: OpenCV colormap to use
            alpha: Blend factor for overlay
        
        Returns:
            Tuple of (heatmap, overlay, predicted_class, confidence)
        """
        # Generate CAM
        cam, pred_class, confidence = self.generate_cam(input_tensor, target_class, frame_idx)
        
        # Resize CAM to match frame size
        cam_resized = cv2.resize(cam, (original_frame.shape[1], original_frame.shape[0]))
        
        # Convert to heatmap
        heatmap = np.uint8(255 * cam_resized)
        heatmap_colored = cv2.applyColorMap(heatmap, colormap)
        
        # Ensure original frame is in correct format
        if original_frame.max() <= 1.0:
            original_frame = (original_frame * 255).astype(np.uint8)
        
        # Create overlay
        overlay = cv2.addWeighted(original_frame.astype(np.uint8), 1 - alpha, 
                                  heatmap_colored, alpha, 0)
        
        return heatmap_colored, overlay, pred_class, confidence
    
    def cleanup(self) -> None:
        """Remove hooks to prevent memory leaks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []
        self.gradients = None
        self.activations = None


def generate_gradcam_heatmap(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    original_frame: np.ndarray,
    save_path: Optional[str] = None,
    frame_idx: int = -1
) -> Dict[str, Any]:
    """
    Convenience function to generate Grad-CAM heatmap for a single frame.
    
    Args:
        model: Deepfake detection model
        input_tensor: Model input tensor
        original_frame: Original frame numpy array
        save_path: Optional path to save heatmap image
        frame_idx: Frame index to explain
    
    Returns:
        Dictionary with heatmap, overlay, prediction, confidence, and save path
    """
    explainer = GradCAMExplainer(model)
    
    try:
        heatmap, overlay, pred_class, confidence = explainer.generate_heatmap_overlay(
            input_tensor, original_frame, frame_idx=frame_idx
        )
        
        result = {
            'heatmap': heatmap,
            'overlay': overlay,
            'predicted_class': pred_class,
            'prediction_label': 'FAKE' if pred_class == 0 else 'REAL',
            'confidence': confidence * 100,
            'frame_idx': frame_idx,
            'save_path': None
        }
        
        if save_path:
            cv2.imwrite(save_path, overlay)
            result['save_path'] = save_path
        
        return result
    
    finally:
        explainer.cleanup()


def generate_sequence_gradcam(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    original_frames: List[np.ndarray],
    output_dir: str,
    video_name: str = "video"
) -> List[Dict[str, Any]]:
    """
    Generate Grad-CAM heatmaps for all frames in a sequence.
    
    Args:
        model: Deepfake detection model
        input_tensor: Model input tensor (batch, seq_len, c, h, w)
        original_frames: List of original frame numpy arrays
        output_dir: Directory to save heatmap images
        video_name: Base name for output files
    
    Returns:
        List of result dictionaries for each frame
    """
    os.makedirs(output_dir, exist_ok=True)
    
    explainer = GradCAMExplainer(model)
    results = []
    
    try:
        seq_length = min(input_tensor.shape[1], len(original_frames))
        
        for frame_idx in range(seq_length):
            heatmap, overlay, pred_class, confidence = explainer.generate_heatmap_overlay(
                input_tensor, original_frames[frame_idx], frame_idx=frame_idx
            )
            
            save_path = os.path.join(output_dir, f"{video_name}_gradcam_frame_{frame_idx:04d}.png")
            cv2.imwrite(save_path, overlay)
            
            results.append({
                'frame_idx': frame_idx,
                'heatmap': heatmap,
                'overlay': overlay,
                'predicted_class': pred_class,
                'prediction_label': 'FAKE' if pred_class == 0 else 'REAL',
                'confidence': confidence * 100,
                'save_path': save_path
            })
    
    finally:
        explainer.cleanup()
    
    return results

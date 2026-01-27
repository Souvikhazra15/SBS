"""
Deepfake Detection Service - Real PyTorch Model Implementation

Uses trained CNN/LSTM model for detecting deepfakes in videos and images.
Auto-downloads model from Google Drive if not present.
"""

from __future__ import annotations
import base64
import io
import time
import logging
import os
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from PIL import Image
import numpy as np
import cv2
from datetime import datetime

if TYPE_CHECKING:
    import torch

logger = logging.getLogger(__name__)

# Lazy imports for heavy dependencies
torch = None
gdown = None

class DeepfakeService:
    """Service for detecting deepfakes using trained PyTorch model."""
    
    # Google Drive model details
    MODEL_GDRIVE_ID = "1HqH15cM_Aye4lWLnO4JjMAapgGmOA6Fl"
    MODEL_URL = f"https://drive.google.com/uc?id={MODEL_GDRIVE_ID}"
    MODEL_FILENAME = "deepfake_model.pt"
    
    def __init__(self):
        self.model_version = "DeepFakeNet-v4.1"
        self.detection_threshold = 0.5  # >= 0.5 = FAKE, < 0.5 = REAL
        self.model = None
        self.device = None
        self.model_dir = Path(__file__).parent.parent.parent / "models" / "deepfake"
        self.model_path = self.model_dir / self.MODEL_FILENAME
        
        # Create model directory
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model on init
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize PyTorch model and detect device."""
        global torch, gdown
        
        try:
            # Import torch
            import torch as torch_module
            torch = torch_module
            
            # Detect device
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("[DEEPFAKE] GPU (CUDA) detected and will be used")
            else:
                self.device = torch.device("cpu")
                logger.info("[DEEPFAKE] No GPU detected, using CPU")
            
            # Check if model exists
            if not self.model_path.exists():
                logger.info(f"[DEEPFAKE] Model not found at {self.model_path}")
                self._download_model()
            else:
                logger.info(f"[DEEPFAKE] Model found at {self.model_path}")
            
            # Load model
            logger.info("[DEEPFAKE] Loading model weights...")
            self.model = torch.load(
                str(self.model_path),
                map_location=self.device
            )
            self.model.eval()  # Set to evaluation mode
            self.model.to(self.device)
            
            logger.info(f"[DEEPFAKE] ✓ Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"[DEEPFAKE] ✗ Failed to initialize model: {str(e)}")
            self.model = None
    
    def _download_model(self):
        """Download model from Google Drive."""
        global gdown
        
        try:
            import gdown as gdown_module
            gdown = gdown_module
            
            logger.info(f"[DEEPFAKE] Downloading model from Google Drive...")
            logger.info(f"[DEEPFAKE] URL: {self.MODEL_URL}")
            logger.info(f"[DEEPFAKE] Destination: {self.model_path}")
            
            # Download file
            gdown.download(
                self.MODEL_URL,
                str(self.model_path),
                quiet=False,
                fuzzy=True
            )
            
            # Verify download
            if self.model_path.exists():
                file_size = self.model_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"[DEEPFAKE] ✓ Model downloaded successfully ({file_size:.2f} MB)")
            else:
                raise Exception("Model file not found after download")
                
        except ImportError:
            logger.error("[DEEPFAKE] gdown not installed. Install with: pip install gdown")
            raise Exception("Cannot download model: gdown not installed")
        except Exception as e:
            logger.error(f"[DEEPFAKE] ✗ Model download failed: {str(e)}")
            raise Exception(f"Model download failed: {str(e)}")
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video file for deepfake content.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        try:
            if self.model is None:
                return self._create_error_response("Model not loaded", start_time)
            
            logger.info(f"[DEEPFAKE] Video received: {video_path}")
            
            # Extract frames
            logger.info("[DEEPFAKE] Extracting frames...")
            frames = self._extract_frames(video_path, max_frames=30, fps=10)
            
            if len(frames) == 0:
                return self._create_error_response("No frames extracted from video", start_time)
            
            logger.info(f"[DEEPFAKE] Extracted {len(frames)} frames")
            
            # Preprocess frames
            logger.info("[DEEPFAKE] Preprocessing frames...")
            processed_frames = [self._preprocess_frame(frame) for frame in frames]
            
            # Run inference
            logger.info("[DEEPFAKE] Running model inference...")
            predictions = []
            
            for idx, frame_tensor in enumerate(processed_frames):
                with torch.no_grad():
                    frame_tensor = frame_tensor.to(self.device)
                    output = self.model(frame_tensor)
                    
                    # Get probability (adjust based on model output)
                    if isinstance(output, torch.Tensor):
                        if output.shape[-1] == 1:
                            # Single output (sigmoid)
                            prob = torch.sigmoid(output).item()
                        else:
                            # Binary classification (softmax)
                            prob = torch.softmax(output, dim=-1)[0][1].item()
                    else:
                        prob = float(output)
                    
                    predictions.append(prob)
                    
                    if (idx + 1) % 10 == 0:
                        logger.info(f"[DEEPFAKE] Processed {idx + 1}/{len(processed_frames)} frames")
            
            # Calculate final score
            avg_score = float(np.mean(predictions))
            max_score = float(np.max(predictions))
            min_score = float(np.min(predictions))
            std_score = float(np.std(predictions))
            
            deepfake_score = avg_score
            decision = "FAKE" if deepfake_score >= self.detection_threshold else "REAL"
            
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"[DEEPFAKE] Inference complete - Score: {deepfake_score:.4f}")
            logger.info(f"[DEEPFAKE] Decision: {decision}")
            
            result = {
                "deepfake_score": round(deepfake_score * 100, 2),
                "is_deepfake": decision == "FAKE",
                "decision": decision,
                "confidence_level": round(deepfake_score, 4),
                "frames_analyzed": len(frames),
                "frame_predictions": [round(p * 100, 2) for p in predictions],
                "statistics": {
                    "mean": round(avg_score * 100, 2),
                    "max": round(max_score * 100, 2),
                    "min": round(min_score * 100, 2),
                    "std": round(std_score * 100, 2)
                },
                "processing_time_ms": processing_time,
                "model_version": self.model_version,
                "device": str(self.device),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("[DEEPFAKE] Analysis complete")
            return result
            
        except Exception as e:
            logger.error(f"[DEEPFAKE] Analysis failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_response(str(e), start_time)
    
    def analyze_image(self, image_data: str) -> Dict[str, Any]:
        """
        Analyze single image for deepfake content.
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        try:
            if self.model is None:
                return self._create_error_response("Model not loaded", start_time)
            
            logger.info("[DEEPFAKE] Image received")
            
            # Decode image
            image = self._decode_image(image_data)
            
            # Preprocess
            processed_frame = self._preprocess_frame(image)
            
            # Run inference
            logger.info("[DEEPFAKE] Running model inference...")
            with torch.no_grad():
                processed_frame = processed_frame.to(self.device)
                output = self.model(processed_frame)
                
                # Get probability
                if isinstance(output, torch.Tensor):
                    if output.shape[-1] == 1:
                        prob = torch.sigmoid(output).item()
                    else:
                        prob = torch.softmax(output, dim=-1)[0][1].item()
                else:
                    prob = float(output)
            
            deepfake_score = float(prob)
            decision = "FAKE" if deepfake_score >= self.detection_threshold else "REAL"
            
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"[DEEPFAKE] Inference complete - Score: {deepfake_score:.4f}, Decision: {decision}")
            
            return {
                "deepfake_score": round(deepfake_score * 100, 2),
                "is_deepfake": decision == "FAKE",
                "decision": decision,
                "confidence_level": round(deepfake_score, 4),
                "frames_analyzed": 1,
                "processing_time_ms": processing_time,
                "model_version": self.model_version,
                "device": str(self.device),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[DEEPFAKE] Analysis failed: {str(e)}")
            return self._create_error_response(str(e), start_time)
    
    def _extract_frames(self, video_path: str, max_frames: int = 30, fps: int = 10) -> List[np.ndarray]:
        """Extract frames from video."""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error("[DEEPFAKE] Failed to open video file")
            return frames
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame interval
        if total_frames > max_frames:
            interval = total_frames // max_frames
        else:
            interval = 1
        
        frame_idx = 0
        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            
            frame_idx += 1
        
        cap.release()
        logger.info(f"[DEEPFAKE] Extracted {len(frames)} frames from {total_frames} total frames")
        
        return frames
    
    def _preprocess_frame(self, frame: np.ndarray) -> torch.Tensor:
        """Preprocess frame for model input."""
        # Resize to model input size (adjust based on model requirements)
        frame_resized = cv2.resize(frame, (224, 224))
        
        # Normalize to [0, 1]
        frame_normalized = frame_resized.astype('float32') / 255.0
        
        # Convert to tensor and add batch dimension
        # Shape: (1, H, W, C) -> (1, C, H, W)
        frame_tensor = torch.from_numpy(frame_normalized).permute(2, 0, 1).unsqueeze(0)
        
        return frame_tensor
    
    def _decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image to numpy array."""
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    def _create_error_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Create standardized error response."""
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "error": error_message,
            "deepfake_score": 0.0,
            "is_deepfake": False,
            "decision": "ERROR",
            "confidence_level": 0.0,
            "processing_time_ms": processing_time
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the deepfake detection model."""
        return {
            "model_version": self.model_version,
            "detection_threshold": self.detection_threshold,
            "model_loaded": self.model is not None,
            "device": str(self.device) if self.device else "not initialized",
            "model_path": str(self.model_path),
            "supported_formats": ["mp4", "avi", "mov", "jpg", "jpeg", "png"],
            "max_file_size": "100MB",
            "recommended_resolution": "720p minimum for video"
        }
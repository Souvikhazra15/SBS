"""
Real-Time Webcam Deepfake Detection Module

Provides live demo capability with:
- Webcam capture using OpenCV
- Real-time face detection
- Configurable inference frequency
- Live fake probability meter
- Warning overlay for high probability
- Frame skipping for latency control

IMPORTANT: This module is additive and does not modify existing inference logic.
"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from typing import Optional, Callable, Dict, Any, Tuple, List
from dataclasses import dataclass
from threading import Thread, Event
from queue import Queue
import time


@dataclass
class DetectionResult:
    """Result from a single detection."""
    frame_index: int
    is_fake: bool
    fake_probability: float
    real_probability: float
    confidence: float
    face_bbox: Optional[Tuple[int, int, int, int]]
    inference_time_ms: float
    timestamp: float


class FrameBuffer:
    """Thread-safe frame buffer for inference queue."""
    
    def __init__(self, max_size: int = 30):
        self.buffer: List[np.ndarray] = []
        self.max_size = max_size
    
    def add_frame(self, frame: np.ndarray) -> None:
        """Add frame to buffer."""
        self.buffer.append(frame.copy())
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)
    
    def get_sequence(self, count: int) -> Optional[List[np.ndarray]]:
        """Get last N frames for inference."""
        if len(self.buffer) >= count:
            return self.buffer[-count:]
        return None
    
    def clear(self) -> None:
        """Clear buffer."""
        self.buffer = []


class WebcamDeepfakeDetector:
    """
    Real-time deepfake detection from webcam feed.
    
    Designed for demo/hackathon scenarios with configurable
    inference frequency and latency control.
    """
    
    def __init__(
        self,
        model: torch.nn.Module,
        transform: Callable,
        sequence_length: int = 20,
        inference_interval: int = 10,
        fake_threshold: float = 0.6,
        device: str = 'cpu'
    ):
        """
        Initialize webcam detector.
        
        Args:
            model: Loaded deepfake detection model
            transform: Frame preprocessing transform
            sequence_length: Number of frames for model input
            inference_interval: Run inference every N frames
            fake_threshold: Probability threshold for FAKE warning
            device: Computation device ('cpu' or 'cuda')
        """
        self.model = model
        self.transform = transform
        self.sequence_length = sequence_length
        self.inference_interval = inference_interval
        self.fake_threshold = fake_threshold
        self.device = device
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # State
        self.frame_buffer = FrameBuffer(max_size=sequence_length * 2)
        self.current_result: Optional[DetectionResult] = None
        self.frame_count = 0
        self.is_running = False
        self.stop_event = Event()
        
        # Statistics
        self.total_inferences = 0
        self.avg_inference_time = 0.0
        self.detection_history: List[DetectionResult] = []
    
    def detect_face(self, frame: np.ndarray, padding: int = 20) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """
        Detect and crop face from frame.
        
        Args:
            frame: BGR image frame
            padding: Padding around face crop
        
        Returns:
            Tuple of (cropped face, bounding box) or (None, None)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
        
        if len(faces) == 0:
            return None, None
        
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        
        # Add padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + w + padding)
        y2 = min(frame.shape[0], y + h + padding)
        
        face_crop = frame[y1:y2, x1:x2]
        
        if face_crop.size == 0:
            return None, None
        
        return face_crop, (x1, y1, x2 - x1, y2 - y1)
    
    def preprocess_sequence(self, frames: List[np.ndarray]) -> Optional[torch.Tensor]:
        """
        Preprocess frame sequence for model input.
        
        Args:
            frames: List of BGR face-cropped frames
        
        Returns:
            Preprocessed tensor or None
        """
        processed = []
        
        for frame in frames:
            # Detect and crop face
            face, _ = self.detect_face(frame)
            if face is None:
                # Use full frame if no face detected
                face = frame
            
            # Apply transform
            try:
                tensor = self.transform(face)
                processed.append(tensor)
            except Exception:
                continue
        
        if len(processed) < self.sequence_length:
            return None
        
        # Stack into sequence
        sequence = torch.stack(processed[-self.sequence_length:])
        return sequence.unsqueeze(0)  # Add batch dimension
    
    def run_inference(self, input_tensor: torch.Tensor) -> DetectionResult:
        """
        Run model inference on input tensor.
        
        Args:
            input_tensor: Preprocessed input tensor
        
        Returns:
            DetectionResult
        """
        start_time = time.time()
        
        self.model.eval()
        with torch.no_grad():
            input_tensor = input_tensor.to(self.device)
            fmap, logits = self.model(input_tensor)
            probs = F.softmax(logits, dim=1)
        
        inference_time = (time.time() - start_time) * 1000
        
        fake_prob = probs[0, 0].item()
        real_prob = probs[0, 1].item()
        is_fake = fake_prob > self.fake_threshold
        
        result = DetectionResult(
            frame_index=self.frame_count,
            is_fake=is_fake,
            fake_probability=fake_prob,
            real_probability=real_prob,
            confidence=max(fake_prob, real_prob) * 100,
            face_bbox=None,
            inference_time_ms=inference_time,
            timestamp=time.time()
        )
        
        # Update statistics
        self.total_inferences += 1
        self.avg_inference_time = (
            (self.avg_inference_time * (self.total_inferences - 1) + inference_time) 
            / self.total_inferences
        )
        
        self.detection_history.append(result)
        
        return result
    
    def draw_overlay(
        self,
        frame: np.ndarray,
        result: Optional[DetectionResult],
        face_bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> np.ndarray:
        """
        Draw detection overlay on frame.
        
        Args:
            frame: BGR image frame
            result: Detection result
            face_bbox: Face bounding box
        
        Returns:
            Frame with overlay
        """
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Draw face bounding box
        if face_bbox is not None:
            x, y, bw, bh = face_bbox
            if result and result.is_fake:
                color = (0, 0, 255)  # Red for fake
            else:
                color = (0, 255, 0)  # Green for real
            cv2.rectangle(output, (x, y), (x + bw, y + bh), color, 2)
        
        if result is None:
            # Show "Analyzing..." message
            cv2.putText(output, "Analyzing...", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            return output
        
        # Status bar background
        cv2.rectangle(output, (0, 0), (w, 80), (0, 0, 0), -1)
        
        # Status text
        if result.is_fake:
            status = "FAKE DETECTED"
            status_color = (0, 0, 255)
        else:
            status = "REAL"
            status_color = (0, 255, 0)
        
        cv2.putText(output, status, (10, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
        
        # Probability bar
        bar_width = 300
        bar_height = 20
        bar_x = 10
        bar_y = 50
        
        # Background
        cv2.rectangle(output, (bar_x, bar_y), 
                     (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Fake probability fill
        fake_fill = int(result.fake_probability * bar_width)
        cv2.rectangle(output, (bar_x, bar_y), 
                     (bar_x + fake_fill, bar_y + bar_height), (0, 0, 255), -1)
        
        # Threshold line
        threshold_x = bar_x + int(self.fake_threshold * bar_width)
        cv2.line(output, (threshold_x, bar_y - 5), 
                (threshold_x, bar_y + bar_height + 5), (255, 255, 255), 2)
        
        # Probability text
        prob_text = f"Fake: {result.fake_probability * 100:.1f}%"
        cv2.putText(output, prob_text, (bar_x + bar_width + 10, bar_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Inference time
        time_text = f"Inference: {result.inference_time_ms:.1f}ms"
        cv2.putText(output, time_text, (w - 200, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Warning overlay for high fake probability
        if result.fake_probability > 0.8:
            # Add red tint
            overlay = output.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 100), -1)
            output = cv2.addWeighted(output, 0.8, overlay, 0.2, 0)
            
            # Warning text
            cv2.putText(output, "! HIGH PROBABILITY DEEPFAKE !", 
                       (w // 2 - 200, h // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        
        return output
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[DetectionResult]]:
        """
        Process a single frame from webcam.
        
        Args:
            frame: BGR image frame
        
        Returns:
            Tuple of (annotated frame, detection result if inference was run)
        """
        self.frame_count += 1
        
        # Detect face for visualization
        _, face_bbox = self.detect_face(frame)
        
        # Add to buffer
        self.frame_buffer.add_frame(frame)
        
        result = None
        
        # Run inference at specified interval
        if self.frame_count % self.inference_interval == 0:
            frames = self.frame_buffer.get_sequence(self.sequence_length)
            if frames is not None:
                input_tensor = self.preprocess_sequence(frames)
                if input_tensor is not None:
                    result = self.run_inference(input_tensor)
                    result.face_bbox = face_bbox
                    self.current_result = result
        
        # Draw overlay with current/cached result
        annotated = self.draw_overlay(frame, self.current_result, face_bbox)
        
        return annotated, result
    
    def run_webcam(
        self,
        camera_id: int = 0,
        window_name: str = "Deepfake Detection - Press 'q' to quit",
        max_frames: Optional[int] = None
    ) -> List[DetectionResult]:
        """
        Run real-time detection on webcam feed.
        
        Args:
            camera_id: Camera device ID
            window_name: Display window name
            max_frames: Maximum frames to process (None = unlimited)
        
        Returns:
            List of detection results
        """
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera {camera_id}")
        
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_running = True
        self.stop_event.clear()
        
        try:
            while self.is_running and not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                annotated, result = self.process_frame(frame)
                
                # Display
                cv2.imshow(window_name, annotated)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                if max_frames and self.frame_count >= max_frames:
                    break
        
        finally:
            self.is_running = False
            cap.release()
            cv2.destroyAllWindows()
        
        return self.detection_history
    
    def stop(self) -> None:
        """Stop webcam detection."""
        self.stop_event.set()
        self.is_running = False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        if not self.detection_history:
            return {
                'total_frames': self.frame_count,
                'total_inferences': 0,
                'avg_inference_time_ms': 0,
                'fake_detections': 0,
                'real_detections': 0,
                'avg_fake_probability': 0
            }
        
        fake_count = sum(1 for r in self.detection_history if r.is_fake)
        real_count = len(self.detection_history) - fake_count
        avg_fake_prob = np.mean([r.fake_probability for r in self.detection_history])
        
        return {
            'total_frames': self.frame_count,
            'total_inferences': self.total_inferences,
            'avg_inference_time_ms': self.avg_inference_time,
            'fake_detections': fake_count,
            'real_detections': real_count,
            'avg_fake_probability': float(avg_fake_prob),
            'fake_percentage': float(fake_count / len(self.detection_history) * 100)
        }
    
    def reset(self) -> None:
        """Reset detector state."""
        self.frame_buffer.clear()
        self.current_result = None
        self.frame_count = 0
        self.total_inferences = 0
        self.avg_inference_time = 0.0
        self.detection_history = []


def create_webcam_detector(
    model: torch.nn.Module,
    transform: Callable,
    sequence_length: int = 20,
    inference_interval: int = 15,
    fake_threshold: float = 0.6
) -> WebcamDeepfakeDetector:
    """
    Factory function to create webcam detector.
    
    Args:
        model: Loaded deepfake model
        transform: Frame transform
        sequence_length: Sequence length for model
        inference_interval: Inference every N frames
        fake_threshold: Threshold for fake detection
    
    Returns:
        Configured WebcamDeepfakeDetector
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    return WebcamDeepfakeDetector(
        model=model,
        transform=transform,
        sequence_length=sequence_length,
        inference_interval=inference_interval,
        fake_threshold=fake_threshold,
        device=device
    )

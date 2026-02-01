"""
Frame-wise Fake Probability Timeline Module

Exposes temporal inconsistency by tracking per-frame deepfake probability.
Outputs JSON data compatible with Chart.js for visualization.

IMPORTANT: This module is non-blocking and does not modify inference logic.
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from datetime import datetime


@dataclass
class FrameProbability:
    """Data class for frame probability information."""
    frame_index: int
    fake_probability: float
    real_probability: float
    timestamp_ms: float
    is_anomaly: bool = False
    anomaly_score: float = 0.0


class FrameProbabilityTimeline:
    """
    Tracks frame-wise deepfake probabilities for temporal analysis.
    
    Designed to be non-blocking and plug into existing inference pipeline.
    """
    
    def __init__(
        self,
        fps: float = 30.0,
        anomaly_threshold: float = 0.3,
        smoothing_window: int = 5
    ):
        """
        Initialize timeline tracker.
        
        Args:
            fps: Frames per second of the video
            anomaly_threshold: Threshold for detecting probability anomalies
            smoothing_window: Window size for moving average smoothing
        """
        self.fps = fps
        self.anomaly_threshold = anomaly_threshold
        self.smoothing_window = smoothing_window
        self.frame_data: List[FrameProbability] = []
        self.metadata: Dict[str, Any] = {}
    
    def reset(self) -> None:
        """Reset timeline data for new video."""
        self.frame_data = []
        self.metadata = {}
    
    def add_frame(
        self,
        frame_index: int,
        logits: torch.Tensor,
        timestamp_ms: Optional[float] = None
    ) -> FrameProbability:
        """
        Add frame probability to timeline.
        
        Args:
            frame_index: Index of the frame
            logits: Model output logits (before softmax)
            timestamp_ms: Optional timestamp in milliseconds
        
        Returns:
            FrameProbability object for the added frame
        """
        # Apply softmax to get probabilities
        probs = F.softmax(logits, dim=-1)
        
        # Handle different tensor shapes
        if probs.dim() > 1:
            probs = probs.squeeze()
        
        fake_prob = probs[0].item() if probs.numel() > 1 else probs.item()
        real_prob = probs[1].item() if probs.numel() > 1 else 1 - fake_prob
        
        # Calculate timestamp if not provided
        if timestamp_ms is None:
            timestamp_ms = (frame_index / self.fps) * 1000
        
        # Create frame data
        frame_prob = FrameProbability(
            frame_index=frame_index,
            fake_probability=fake_prob,
            real_probability=real_prob,
            timestamp_ms=timestamp_ms
        )
        
        self.frame_data.append(frame_prob)
        
        # Detect anomalies
        self._detect_anomaly(len(self.frame_data) - 1)
        
        return frame_prob
    
    def add_batch(
        self,
        start_frame: int,
        logits_sequence: torch.Tensor,
        fps: Optional[float] = None
    ) -> List[FrameProbability]:
        """
        Add multiple frames from a batch prediction.
        
        Args:
            start_frame: Starting frame index
            logits_sequence: Sequence of logits (seq_len, num_classes) or (batch, seq_len, num_classes)
            fps: Optional override for fps
        
        Returns:
            List of FrameProbability objects
        """
        if fps is not None:
            self.fps = fps
        
        # Handle different tensor shapes
        if logits_sequence.dim() == 3:
            logits_sequence = logits_sequence.squeeze(0)
        
        results = []
        for i, logits in enumerate(logits_sequence):
            frame_prob = self.add_frame(start_frame + i, logits)
            results.append(frame_prob)
        
        return results
    
    def _detect_anomaly(self, index: int) -> None:
        """Detect probability anomalies based on temporal consistency."""
        if len(self.frame_data) < 2:
            return
        
        current = self.frame_data[index]
        
        # Calculate change from previous frame
        prev = self.frame_data[index - 1]
        change = abs(current.fake_probability - prev.fake_probability)
        
        # Check if change exceeds threshold
        if change > self.anomaly_threshold:
            current.is_anomaly = True
            current.anomaly_score = change
    
    def get_smoothed_probabilities(self) -> List[float]:
        """Get moving-average smoothed fake probabilities."""
        if not self.frame_data:
            return []
        
        probs = [f.fake_probability for f in self.frame_data]
        
        if len(probs) < self.smoothing_window:
            return probs
        
        smoothed = []
        for i in range(len(probs)):
            start = max(0, i - self.smoothing_window // 2)
            end = min(len(probs), i + self.smoothing_window // 2 + 1)
            smoothed.append(np.mean(probs[start:end]))
        
        return smoothed
    
    def get_temporal_stats(self) -> Dict[str, float]:
        """Calculate temporal statistics for the probability timeline."""
        if not self.frame_data:
            return {}
        
        probs = [f.fake_probability for f in self.frame_data]
        
        # Calculate statistics
        mean_prob = np.mean(probs)
        std_prob = np.std(probs)
        max_prob = np.max(probs)
        min_prob = np.min(probs)
        
        # Calculate temporal variance (how much probability changes over time)
        if len(probs) > 1:
            temporal_variance = np.mean([abs(probs[i] - probs[i-1]) for i in range(1, len(probs))])
        else:
            temporal_variance = 0.0
        
        # Count anomalies
        anomaly_count = sum(1 for f in self.frame_data if f.is_anomaly)
        anomaly_ratio = anomaly_count / len(self.frame_data)
        
        # Temporal consistency score (lower variance = higher consistency)
        temporal_consistency = max(0, 100 * (1 - temporal_variance / 0.5))
        
        return {
            'mean_fake_probability': float(mean_prob),
            'std_fake_probability': float(std_prob),
            'max_fake_probability': float(max_prob),
            'min_fake_probability': float(min_prob),
            'temporal_variance': float(temporal_variance),
            'temporal_consistency_score': float(temporal_consistency),
            'anomaly_count': anomaly_count,
            'anomaly_ratio': float(anomaly_ratio),
            'total_frames': len(self.frame_data)
        }
    
    def to_chartjs_data(self) -> Dict[str, Any]:
        """
        Export timeline data in Chart.js compatible format.
        
        Returns:
            Dictionary ready for JSON serialization and Chart.js consumption
        """
        if not self.frame_data:
            return {'labels': [], 'datasets': []}
        
        labels = [f"Frame {f.frame_index}" for f in self.frame_data]
        timestamps = [f.timestamp_ms / 1000 for f in self.frame_data]  # Convert to seconds
        
        fake_probs = [f.fake_probability * 100 for f in self.frame_data]
        real_probs = [f.real_probability * 100 for f in self.frame_data]
        smoothed = [p * 100 for p in self.get_smoothed_probabilities()]
        
        # Mark anomalies
        anomaly_points = [
            {'x': f.frame_index, 'y': f.fake_probability * 100}
            for f in self.frame_data if f.is_anomaly
        ]
        
        return {
            'labels': labels,
            'timestamps': timestamps,
            'datasets': [
                {
                    'label': 'Fake Probability (%)',
                    'data': fake_probs,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'fill': True,
                    'tension': 0.1
                },
                {
                    'label': 'Real Probability (%)',
                    'data': real_probs,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'fill': True,
                    'tension': 0.1
                },
                {
                    'label': 'Smoothed Fake Probability (%)',
                    'data': smoothed,
                    'borderColor': 'rgb(255, 159, 64)',
                    'borderDash': [5, 5],
                    'fill': False,
                    'tension': 0.3
                }
            ],
            'anomalies': anomaly_points,
            'statistics': self.get_temporal_stats()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export timeline data as JSON string."""
        return json.dumps(self.to_chartjs_data(), indent=indent)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export full timeline data as dictionary."""
        return {
            'frames': [asdict(f) for f in self.frame_data],
            'chartjs_data': self.to_chartjs_data(),
            'metadata': {
                'fps': self.fps,
                'total_frames': len(self.frame_data),
                'duration_seconds': len(self.frame_data) / self.fps if self.fps > 0 else 0,
                'generated_at': datetime.now().isoformat()
            }
        }


def extract_frame_probabilities_from_model(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    fps: float = 30.0
) -> FrameProbabilityTimeline:
    """
    Extract per-frame probabilities from model prediction.
    
    This function hooks into the model's intermediate outputs to extract
    frame-wise probabilities without modifying the model.
    
    Args:
        model: The deepfake detection model
        input_tensor: Input tensor (batch, seq_len, c, h, w)
        fps: Video FPS for timestamp calculation
    
    Returns:
        FrameProbabilityTimeline with per-frame probabilities
    """
    timeline = FrameProbabilityTimeline(fps=fps)
    
    model.eval()
    
    with torch.no_grad():
        # Get model outputs
        fmap, logits = model(input_tensor)
        
        # The model uses LSTM, so we need per-frame analysis
        # Re-run through CNN to get per-frame features
        batch_size, seq_length = input_tensor.shape[:2]
        
        # Get the linear layer weights for computing per-frame scores
        linear_weights = model.linear1.weight.detach()
        linear_bias = model.linear1.bias.detach() if model.linear1.bias is not None else None
        
        # Reshape input for per-frame processing
        x = input_tensor.view(batch_size * seq_length, *input_tensor.shape[2:])
        
        # Get per-frame features from CNN
        features = model.model(x)  # (batch*seq, channels, h, w)
        features = model.avgpool(features)  # (batch*seq, channels, 1, 1)
        features = features.view(batch_size, seq_length, -1)  # (batch, seq, features)
        
        # Compute per-frame logits (without LSTM temporal modeling)
        # This gives us raw per-frame predictions
        for i in range(seq_length):
            frame_features = features[0, i]  # (features,)
            frame_logits = F.linear(frame_features, linear_weights, linear_bias)
            timeline.add_frame(i, frame_logits)
    
    return timeline

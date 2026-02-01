"""
Deepfake Forensics Dashboard Module

Computes forensic metrics for deepfake investigation:
- Face consistency score across frames
- Eye blink rate detection
- Temporal stability score
- Compression artifact estimation

IMPORTANT: Uses only OpenCV + NumPy. No mock values. All scores normalized to 0-100.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import os


@dataclass
class ForensicsMetrics:
    """Complete forensics analysis results."""
    face_consistency_score: float  # 0-100
    eye_blink_rate: float  # blinks per second
    eye_blink_score: float  # 0-100 (abnormal = lower)
    temporal_stability_score: float  # 0-100
    compression_artifact_score: float  # 0-100 (higher = more artifacts)
    blockiness_index: float  # Raw blockiness measure
    frequency_anomaly_score: float  # 0-100
    overall_forensics_score: float  # 0-100 composite
    frame_count: int
    faces_detected: int
    analysis_details: Dict[str, Any]


class FaceConsistencyAnalyzer:
    """Analyzes face consistency across video frames."""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.face_features: List[np.ndarray] = []
        self.face_sizes: List[Tuple[int, int]] = []
        self.face_positions: List[Tuple[int, int]] = []
    
    def reset(self) -> None:
        """Reset analyzer state."""
        self.face_features = []
        self.face_sizes = []
        self.face_positions = []
    
    def add_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Add a frame for face consistency analysis.
        
        Args:
            frame: BGR image frame
        
        Returns:
            Face detection info or None if no face found
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        
        if len(faces) == 0:
            return None
        
        # Use the largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size == 0:
            return None
        
        # Resize to standard size for comparison
        face_resized = cv2.resize(face_roi, (64, 64))
        
        # Compute histogram features
        hist = cv2.calcHist([face_resized], [0], None, [64], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        self.face_features.append(hist)
        self.face_sizes.append((w, h))
        self.face_positions.append((x + w//2, y + h//2))
        
        return {
            'bbox': (x, y, w, h),
            'center': (x + w//2, y + h//2),
            'size': (w, h)
        }
    
    def compute_consistency_score(self) -> Tuple[float, Dict[str, Any]]:
        """
        Compute face consistency score.
        
        Returns:
            Tuple of (score 0-100, analysis details)
        """
        if len(self.face_features) < 2:
            return 100.0, {'reason': 'Insufficient frames for analysis'}
        
        # Feature similarity using histogram correlation
        similarities = []
        for i in range(1, len(self.face_features)):
            corr = cv2.compareHist(
                self.face_features[i].astype(np.float32),
                self.face_features[i-1].astype(np.float32),
                cv2.HISTCMP_CORREL
            )
            similarities.append(max(0, corr))
        
        mean_similarity = np.mean(similarities)
        
        # Size consistency
        sizes = np.array(self.face_sizes)
        size_variance = np.std(sizes[:, 0]) / (np.mean(sizes[:, 0]) + 1e-6)
        
        # Position consistency (relative movement)
        positions = np.array(self.face_positions)
        if len(positions) > 1:
            movements = np.sqrt(np.sum(np.diff(positions, axis=0)**2, axis=1))
            movement_variance = np.std(movements) / (np.mean(movements) + 1e-6)
        else:
            movement_variance = 0.0
        
        # Combine into score (higher = more consistent)
        feature_score = mean_similarity * 100
        size_score = max(0, 100 - size_variance * 200)
        position_score = max(0, 100 - movement_variance * 50)
        
        consistency_score = (feature_score * 0.5 + size_score * 0.25 + position_score * 0.25)
        
        details = {
            'mean_feature_similarity': float(mean_similarity),
            'size_variance_ratio': float(size_variance),
            'movement_variance_ratio': float(movement_variance),
            'component_scores': {
                'feature': float(feature_score),
                'size': float(size_score),
                'position': float(position_score)
            },
            'frames_analyzed': len(self.face_features)
        }
        
        return float(np.clip(consistency_score, 0, 100)), details


class EyeBlinkDetector:
    """Detects eye blinks for liveness analysis."""
    
    # Eye aspect ratio threshold for blink detection
    EAR_THRESHOLD = 0.2
    CONSECUTIVE_FRAMES = 2
    
    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.ear_history: List[float] = []
        self.blink_count = 0
        self.consecutive_closed = 0
        self.frame_count = 0
    
    def reset(self) -> None:
        """Reset detector state."""
        self.ear_history = []
        self.blink_count = 0
        self.consecutive_closed = 0
        self.frame_count = 0
    
    def _compute_eye_aspect_ratio(self, eye_region: np.ndarray) -> float:
        """Compute approximate eye aspect ratio from eye region."""
        if eye_region.size == 0:
            return 0.5  # Default neutral value
        
        # Use contour-based approach
        gray = eye_region if len(eye_region.shape) == 2 else cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
        
        # Threshold to find eye opening
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 0.5
        
        # Get the largest contour (likely the eye opening)
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        # Aspect ratio approximation
        if w == 0:
            return 0.5
        ear = h / w
        
        return float(ear)
    
    def add_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a frame for blink detection.
        
        Args:
            frame: BGR image frame
        
        Returns:
            Detection info including eyes found and EAR
        """
        self.frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect face first
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        
        if len(faces) == 0:
            return {'eyes_found': 0, 'ear': None}
        
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_roi = gray[y:y+h, x:x+w]
        
        # Detect eyes in face region
        eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 3, minSize=(20, 20))
        
        if len(eyes) < 2:
            self.ear_history.append(0.3)  # Likely closed/not visible
            self.consecutive_closed += 1
            if self.consecutive_closed >= self.CONSECUTIVE_FRAMES:
                # Check if this could be a blink
                if len(self.ear_history) >= self.CONSECUTIVE_FRAMES + 2:
                    prev_open = np.mean(self.ear_history[-self.CONSECUTIVE_FRAMES-2:-self.CONSECUTIVE_FRAMES])
                    if prev_open > self.EAR_THRESHOLD * 1.5:
                        self.blink_count += 1
                        self.consecutive_closed = 0
            return {'eyes_found': len(eyes), 'ear': 0.3}
        
        # Compute EAR for detected eyes
        ears = []
        for (ex, ey, ew, eh) in eyes[:2]:  # Use up to 2 eyes
            eye_roi = face_roi[ey:ey+eh, ex:ex+ew]
            ear = self._compute_eye_aspect_ratio(eye_roi)
            ears.append(ear)
        
        avg_ear = np.mean(ears)
        self.ear_history.append(avg_ear)
        
        # Blink detection
        if avg_ear < self.EAR_THRESHOLD:
            self.consecutive_closed += 1
        else:
            if self.consecutive_closed >= self.CONSECUTIVE_FRAMES:
                self.blink_count += 1
            self.consecutive_closed = 0
        
        return {'eyes_found': len(eyes), 'ear': float(avg_ear)}
    
    def compute_blink_rate(self, fps: float = 30.0) -> Tuple[float, float, Dict[str, Any]]:
        """
        Compute blink rate and score.
        
        Args:
            fps: Video frame rate
        
        Returns:
            Tuple of (blinks per second, score 0-100, details)
        """
        if self.frame_count == 0:
            return 0.0, 50.0, {'reason': 'No frames processed'}
        
        duration_seconds = self.frame_count / fps
        if duration_seconds == 0:
            return 0.0, 50.0, {'reason': 'Zero duration'}
        
        blinks_per_second = self.blink_count / duration_seconds
        blinks_per_minute = blinks_per_second * 60
        
        # Normal human blink rate: 15-20 per minute
        # Score based on deviation from normal
        normal_rate = 17.0  # blinks per minute
        deviation = abs(blinks_per_minute - normal_rate)
        
        # Score: 100 if normal, decreases with deviation
        # Very low or very high rates are suspicious
        if blinks_per_minute < 5:  # Very low - suspicious
            score = max(0, 30 - (5 - blinks_per_minute) * 6)
        elif blinks_per_minute > 40:  # Very high - suspicious
            score = max(0, 50 - (blinks_per_minute - 40) * 2)
        else:
            score = max(0, 100 - deviation * 3)
        
        details = {
            'blink_count': self.blink_count,
            'duration_seconds': float(duration_seconds),
            'blinks_per_minute': float(blinks_per_minute),
            'normal_range': '15-20 per minute',
            'ear_mean': float(np.mean(self.ear_history)) if self.ear_history else 0,
            'ear_std': float(np.std(self.ear_history)) if self.ear_history else 0
        }
        
        return float(blinks_per_second), float(np.clip(score, 0, 100)), details


class TemporalStabilityAnalyzer:
    """Analyzes temporal stability of video frames."""
    
    def __init__(self):
        self.prev_frame: Optional[np.ndarray] = None
        self.flow_magnitudes: List[float] = []
        self.ssim_values: List[float] = []
    
    def reset(self) -> None:
        """Reset analyzer state."""
        self.prev_frame = None
        self.flow_magnitudes = []
        self.ssim_values = []
    
    def add_frame(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Add frame for temporal analysis.
        
        Args:
            frame: BGR image frame
        
        Returns:
            Frame analysis metrics
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (256, 256))  # Normalize size
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return {'flow_magnitude': 0.0, 'ssim': 1.0}
        
        # Compute optical flow
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_frame, gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Flow magnitude
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mean_magnitude = np.mean(magnitude)
        self.flow_magnitudes.append(mean_magnitude)
        
        # Structural similarity (simplified)
        ssim = self._compute_ssim(self.prev_frame, gray)
        self.ssim_values.append(ssim)
        
        self.prev_frame = gray
        
        return {'flow_magnitude': float(mean_magnitude), 'ssim': float(ssim)}
    
    def _compute_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute simplified structural similarity."""
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)
        
        mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.GaussianBlur(img1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
        
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
                   ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        
        return float(np.mean(ssim_map))
    
    def compute_stability_score(self) -> Tuple[float, Dict[str, Any]]:
        """
        Compute temporal stability score.
        
        Returns:
            Tuple of (score 0-100, details)
        """
        if len(self.flow_magnitudes) < 2:
            return 100.0, {'reason': 'Insufficient frames'}
        
        # Flow consistency
        flow_std = np.std(self.flow_magnitudes)
        flow_mean = np.mean(self.flow_magnitudes)
        flow_cv = flow_std / (flow_mean + 1e-6)  # Coefficient of variation
        
        # SSIM consistency
        ssim_mean = np.mean(self.ssim_values)
        ssim_std = np.std(self.ssim_values)
        
        # Score components
        # Low flow CV = consistent motion = good
        flow_score = max(0, 100 - flow_cv * 100)
        
        # High SSIM mean = good temporal consistency
        ssim_score = ssim_mean * 100
        
        # Low SSIM std = consistent quality
        ssim_consistency_score = max(0, 100 - ssim_std * 500)
        
        # Combined score
        stability_score = flow_score * 0.3 + ssim_score * 0.4 + ssim_consistency_score * 0.3
        
        details = {
            'flow_mean': float(flow_mean),
            'flow_std': float(flow_std),
            'flow_coefficient_variation': float(flow_cv),
            'ssim_mean': float(ssim_mean),
            'ssim_std': float(ssim_std),
            'component_scores': {
                'flow_consistency': float(flow_score),
                'ssim_quality': float(ssim_score),
                'ssim_consistency': float(ssim_consistency_score)
            }
        }
        
        return float(np.clip(stability_score, 0, 100)), details


class CompressionArtifactDetector:
    """Detects compression artifacts indicating potential manipulation."""
    
    def __init__(self):
        self.blockiness_values: List[float] = []
        self.frequency_anomalies: List[float] = []
    
    def reset(self) -> None:
        """Reset detector state."""
        self.blockiness_values = []
        self.frequency_anomalies = []
    
    def add_frame(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Analyze frame for compression artifacts.
        
        Args:
            frame: BGR image frame
        
        Returns:
            Artifact metrics
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Blockiness detection
        blockiness = self._compute_blockiness(gray)
        self.blockiness_values.append(blockiness)
        
        # Frequency domain analysis
        freq_anomaly = self._compute_frequency_anomaly(gray)
        self.frequency_anomalies.append(freq_anomaly)
        
        return {
            'blockiness': float(blockiness),
            'frequency_anomaly': float(freq_anomaly)
        }
    
    def _compute_blockiness(self, gray: np.ndarray, block_size: int = 8) -> float:
        """
        Compute blockiness metric (JPEG artifact detection).
        
        Higher values indicate more blocking artifacts.
        """
        h, w = gray.shape
        
        # Ensure dimensions are divisible by block size
        h_blocks = h // block_size
        w_blocks = w // block_size
        
        if h_blocks < 2 or w_blocks < 2:
            return 0.0
        
        gray = gray[:h_blocks * block_size, :w_blocks * block_size]
        
        # Compute horizontal and vertical block boundary differences
        h_diff = 0.0
        v_diff = 0.0
        
        for i in range(1, h_blocks):
            row_idx = i * block_size
            boundary_diff = np.abs(
                gray[row_idx, :].astype(float) - gray[row_idx - 1, :].astype(float)
            )
            internal_diff = np.abs(
                gray[row_idx - block_size // 2, :].astype(float) - 
                gray[row_idx - block_size // 2 - 1, :].astype(float)
            )
            h_diff += np.mean(boundary_diff) / (np.mean(internal_diff) + 1e-6)
        
        for j in range(1, w_blocks):
            col_idx = j * block_size
            boundary_diff = np.abs(
                gray[:, col_idx].astype(float) - gray[:, col_idx - 1].astype(float)
            )
            internal_diff = np.abs(
                gray[:, col_idx - block_size // 2].astype(float) - 
                gray[:, col_idx - block_size // 2 - 1].astype(float)
            )
            v_diff += np.mean(boundary_diff) / (np.mean(internal_diff) + 1e-6)
        
        blockiness = (h_diff / h_blocks + v_diff / w_blocks) / 2
        return float(blockiness)
    
    def _compute_frequency_anomaly(self, gray: np.ndarray) -> float:
        """
        Analyze frequency domain for anomalies.
        
        Detects unnatural frequency patterns that may indicate manipulation.
        """
        # Resize for consistent analysis
        gray = cv2.resize(gray, (256, 256))
        
        # Compute 2D DFT
        dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # Magnitude spectrum
        magnitude = cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1])
        magnitude = np.log(magnitude + 1)
        
        # Normalize
        magnitude = (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min() + 1e-6)
        
        # Analyze radial frequency distribution
        center = (128, 128)
        y, x = np.ogrid[:256, :256]
        r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        
        # Compute radial profile
        r_max = 128
        radial_profile = []
        for radius in range(5, r_max, 5):
            mask = (r >= radius - 2.5) & (r < radius + 2.5)
            if np.any(mask):
                radial_profile.append(np.mean(magnitude[mask]))
        
        if len(radial_profile) < 3:
            return 0.0
        
        # Detect anomalies in radial profile
        # Natural images have smooth decay; manipulated may have peaks
        profile = np.array(radial_profile)
        diff = np.abs(np.diff(profile))
        anomaly_score = np.std(diff) / (np.mean(np.abs(profile)) + 1e-6)
        
        return float(anomaly_score)
    
    def compute_artifact_score(self) -> Tuple[float, float, Dict[str, Any]]:
        """
        Compute compression artifact scores.
        
        Returns:
            Tuple of (blockiness_score, frequency_score, details)
            Higher scores indicate MORE artifacts (suspicious)
        """
        if not self.blockiness_values:
            return 0.0, 0.0, {'reason': 'No frames analyzed'}
        
        mean_blockiness = np.mean(self.blockiness_values)
        std_blockiness = np.std(self.blockiness_values)
        
        mean_freq_anomaly = np.mean(self.frequency_anomalies)
        std_freq_anomaly = np.std(self.frequency_anomalies)
        
        # Normalize to 0-100 scale
        # Higher blockiness = more suspicious
        blockiness_score = min(100, mean_blockiness * 30)
        
        # Higher frequency anomaly = more suspicious
        frequency_score = min(100, mean_freq_anomaly * 100)
        
        details = {
            'mean_blockiness': float(mean_blockiness),
            'std_blockiness': float(std_blockiness),
            'mean_frequency_anomaly': float(mean_freq_anomaly),
            'std_frequency_anomaly': float(std_freq_anomaly),
            'frames_analyzed': len(self.blockiness_values)
        }
        
        return float(blockiness_score), float(frequency_score), details


class DeepfakeForensicsAnalyzer:
    """
    Complete deepfake forensics analysis suite.
    
    Combines all forensic analysis methods into a unified interface.
    """
    
    def __init__(self, fps: float = 30.0):
        """
        Initialize forensics analyzer.
        
        Args:
            fps: Video frame rate
        """
        self.fps = fps
        self.face_analyzer = FaceConsistencyAnalyzer()
        self.blink_detector = EyeBlinkDetector()
        self.stability_analyzer = TemporalStabilityAnalyzer()
        self.artifact_detector = CompressionArtifactDetector()
        self.frame_count = 0
    
    def reset(self) -> None:
        """Reset all analyzers."""
        self.face_analyzer.reset()
        self.blink_detector.reset()
        self.stability_analyzer.reset()
        self.artifact_detector.reset()
        self.frame_count = 0
    
    def add_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Add frame for forensic analysis.
        
        Args:
            frame: BGR image frame
        
        Returns:
            Per-frame analysis results
        """
        self.frame_count += 1
        
        results = {
            'frame_index': self.frame_count - 1,
            'face': self.face_analyzer.add_frame(frame),
            'blink': self.blink_detector.add_frame(frame),
            'stability': self.stability_analyzer.add_frame(frame),
            'artifacts': self.artifact_detector.add_frame(frame)
        }
        
        return results
    
    def analyze_video(self, video_path: str, max_frames: Optional[int] = None) -> ForensicsMetrics:
        """
        Analyze entire video file.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum frames to analyze (None = all)
        
        Returns:
            Complete forensics metrics
        """
        self.reset()
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if max_frames is not None:
            total_frames = min(total_frames, max_frames)
        
        frame_idx = 0
        while frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            self.add_frame(frame)
            frame_idx += 1
        
        cap.release()
        
        return self.compute_metrics()
    
    def analyze_frames(self, frames: List[np.ndarray]) -> ForensicsMetrics:
        """
        Analyze list of frames.
        
        Args:
            frames: List of BGR image frames
        
        Returns:
            Complete forensics metrics
        """
        self.reset()
        
        for frame in frames:
            self.add_frame(frame)
        
        return self.compute_metrics()
    
    def compute_metrics(self) -> ForensicsMetrics:
        """Compute complete forensics metrics."""
        # Face consistency
        face_score, face_details = self.face_analyzer.compute_consistency_score()
        
        # Eye blink analysis
        blink_rate, blink_score, blink_details = self.blink_detector.compute_blink_rate(self.fps)
        
        # Temporal stability
        stability_score, stability_details = self.stability_analyzer.compute_stability_score()
        
        # Compression artifacts
        blockiness_score, frequency_score, artifact_details = self.artifact_detector.compute_artifact_score()
        
        # Overall forensics score
        # Higher = more likely authentic
        # We invert artifact scores since high artifacts = suspicious
        artifact_combined = (blockiness_score + frequency_score) / 2
        
        overall_score = (
            face_score * 0.25 +
            blink_score * 0.20 +
            stability_score * 0.25 +
            (100 - artifact_combined) * 0.30
        )
        
        return ForensicsMetrics(
            face_consistency_score=face_score,
            eye_blink_rate=blink_rate,
            eye_blink_score=blink_score,
            temporal_stability_score=stability_score,
            compression_artifact_score=artifact_combined,
            blockiness_index=artifact_details.get('mean_blockiness', 0),
            frequency_anomaly_score=frequency_score,
            overall_forensics_score=float(np.clip(overall_score, 0, 100)),
            frame_count=self.frame_count,
            faces_detected=len(self.face_analyzer.face_features),
            analysis_details={
                'face': face_details,
                'blink': blink_details,
                'stability': stability_details,
                'artifacts': artifact_details
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        return asdict(self.compute_metrics())

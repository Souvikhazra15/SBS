"""
Multi-Modal Audio-Video Analysis Module

Provides audio-video consistency analysis for deepfake detection:
- Audio extraction using ffmpeg
- Pitch variance analysis
- Jitter detection
- Lip-sync mismatch detection
- Cross-modal consistency scoring

IMPORTANT: Lightweight implementation, no deep audio models.
All math is explainable.
"""

import cv2
import numpy as np
import subprocess
import tempfile
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json


@dataclass
class AudioFeatures:
    """Extracted audio features."""
    duration_seconds: float
    sample_rate: int
    pitch_mean: float
    pitch_std: float
    pitch_variance_score: float  # 0-100, higher = more variance (suspicious)
    jitter_mean: float
    jitter_score: float  # 0-100, higher = more jitter (suspicious)
    energy_profile: List[float]  # Energy over time
    zero_crossing_rate: float
    spectral_centroid_mean: float
    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class LipSyncFeatures:
    """Lip-sync analysis features."""
    mouth_movement_energy: List[float]
    audio_energy: List[float]
    correlation: float  # -1 to 1
    sync_score: float  # 0-100, higher = better sync
    lag_frames: int  # Detected lag in frames
    mismatch_regions: List[Tuple[float, float]]  # Time regions with mismatch


@dataclass
class MultiModalAnalysis:
    """Complete multi-modal analysis results."""
    audio_features: AudioFeatures
    lip_sync_features: Optional[LipSyncFeatures]
    audio_spoof_score: float  # 0-100, higher = more likely spoofed
    lip_sync_score: float  # 0-100, higher = better sync
    combined_score: float  # 0-100, overall authenticity score
    confidence: float
    analysis_details: Dict[str, Any]


class AudioExtractor:
    """Extract and analyze audio from video files using ffmpeg."""
    
    def __init__(self, ffmpeg_path: str = 'ffmpeg'):
        """
        Initialize audio extractor.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable
        """
        self.ffmpeg_path = ffmpeg_path
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            output_path: Optional output path for audio file
        
        Returns:
            Path to extracted audio file or None on failure
        """
        if output_path is None:
            # Create temporary file
            fd, output_path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
        
        try:
            # Extract audio using ffmpeg
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM format
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return None
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            
            return None
        
        except Exception:
            return None
    
    def load_audio_data(self, audio_path: str) -> Tuple[Optional[np.ndarray], int]:
        """
        Load audio data from WAV file using numpy.
        
        Args:
            audio_path: Path to WAV file
        
        Returns:
            Tuple of (audio samples, sample rate)
        """
        try:
            # Read WAV file header and data manually
            with open(audio_path, 'rb') as f:
                # Read RIFF header
                riff = f.read(4)
                if riff != b'RIFF':
                    return None, 0
                
                f.read(4)  # File size
                wave = f.read(4)
                if wave != b'WAVE':
                    return None, 0
                
                # Find fmt chunk
                while True:
                    chunk_id = f.read(4)
                    if len(chunk_id) < 4:
                        return None, 0
                    chunk_size = int.from_bytes(f.read(4), 'little')
                    
                    if chunk_id == b'fmt ':
                        audio_format = int.from_bytes(f.read(2), 'little')
                        num_channels = int.from_bytes(f.read(2), 'little')
                        sample_rate = int.from_bytes(f.read(4), 'little')
                        f.read(6)  # byte rate, block align
                        bits_per_sample = int.from_bytes(f.read(2), 'little')
                        f.read(chunk_size - 16)  # Skip remaining
                        break
                    else:
                        f.read(chunk_size)
                
                # Find data chunk
                while True:
                    chunk_id = f.read(4)
                    if len(chunk_id) < 4:
                        return None, 0
                    chunk_size = int.from_bytes(f.read(4), 'little')
                    
                    if chunk_id == b'data':
                        audio_data = np.frombuffer(f.read(chunk_size), dtype=np.int16)
                        break
                    else:
                        f.read(chunk_size)
                
                # Normalize to float
                audio_samples = audio_data.astype(np.float32) / 32768.0
                
                return audio_samples, sample_rate
        
        except Exception:
            return None, 0


class AudioAnalyzer:
    """Analyze audio for spoofing indicators."""
    
    def __init__(self):
        self.extractor = AudioExtractor()
    
    def compute_pitch_features(
        self,
        audio: np.ndarray,
        sample_rate: int,
        frame_size: int = 1024,
        hop_size: int = 512
    ) -> Tuple[float, float, float]:
        """
        Compute pitch-related features using autocorrelation.
        
        Args:
            audio: Audio samples
            sample_rate: Sample rate
            frame_size: Analysis frame size
            hop_size: Hop size between frames
        
        Returns:
            Tuple of (pitch_mean, pitch_std, pitch_variance_score)
        """
        pitches = []
        
        for i in range(0, len(audio) - frame_size, hop_size):
            frame = audio[i:i + frame_size]
            
            # Autocorrelation-based pitch detection
            corr = np.correlate(frame, frame, mode='full')
            corr = corr[len(corr) // 2:]
            
            # Find first peak after lag 0
            min_lag = sample_rate // 500  # Max 500 Hz
            max_lag = sample_rate // 50   # Min 50 Hz
            
            if max_lag > len(corr):
                continue
            
            search_region = corr[min_lag:max_lag]
            if len(search_region) == 0:
                continue
            
            peak_idx = np.argmax(search_region) + min_lag
            
            if peak_idx > 0 and corr[peak_idx] > 0.3 * corr[0]:
                pitch = sample_rate / peak_idx
                if 50 < pitch < 500:  # Human voice range
                    pitches.append(pitch)
        
        if not pitches:
            return 0.0, 0.0, 50.0  # Neutral score
        
        pitch_mean = np.mean(pitches)
        pitch_std = np.std(pitches)
        
        # Variance score: high variance might indicate unnatural speech
        # Normal speech has moderate pitch variation
        cv = pitch_std / (pitch_mean + 1e-6)  # Coefficient of variation
        
        # Score: 0-100, higher = more suspicious
        if cv < 0.05:  # Too stable - possibly synthetic
            variance_score = 70 + (0.05 - cv) * 600
        elif cv > 0.3:  # Too variable - possibly manipulated
            variance_score = 50 + (cv - 0.3) * 100
        else:  # Normal range
            variance_score = cv * 100
        
        return float(pitch_mean), float(pitch_std), float(np.clip(variance_score, 0, 100))
    
    def compute_jitter(
        self,
        audio: np.ndarray,
        sample_rate: int,
        frame_size: int = 1024
    ) -> Tuple[float, float]:
        """
        Compute jitter (pitch period variation).
        
        Args:
            audio: Audio samples
            sample_rate: Sample rate
            frame_size: Frame size
        
        Returns:
            Tuple of (jitter_mean, jitter_score)
        """
        periods = []
        
        # Simple zero-crossing based period estimation
        zero_crossings = np.where(np.diff(np.signbit(audio)))[0]
        
        if len(zero_crossings) < 4:
            return 0.0, 50.0
        
        # Estimate periods from zero crossings (every 2 crossings ≈ 1 period)
        for i in range(0, len(zero_crossings) - 2, 2):
            period = zero_crossings[i + 2] - zero_crossings[i]
            if 32 < period < 640:  # Valid period range for speech
                periods.append(period)
        
        if len(periods) < 3:
            return 0.0, 50.0
        
        periods = np.array(periods)
        
        # Jitter = mean absolute difference between consecutive periods
        period_diffs = np.abs(np.diff(periods))
        jitter = np.mean(period_diffs) / (np.mean(periods) + 1e-6)
        
        # Normal jitter is < 1%, synthetic might be too perfect (< 0.1%) 
        # or manipulated (> 2%)
        if jitter < 0.001:  # Too perfect
            jitter_score = 80
        elif jitter > 0.02:  # Too variable
            jitter_score = min(100, 50 + jitter * 1000)
        else:
            jitter_score = jitter * 2500  # 0.01 -> 25
        
        return float(jitter), float(np.clip(jitter_score, 0, 100))
    
    def compute_energy_profile(
        self,
        audio: np.ndarray,
        num_segments: int = 50
    ) -> List[float]:
        """
        Compute energy profile over time.
        
        Args:
            audio: Audio samples
            num_segments: Number of segments
        
        Returns:
            List of energy values per segment
        """
        segment_size = len(audio) // num_segments
        if segment_size == 0:
            return []
        
        energy = []
        for i in range(num_segments):
            start = i * segment_size
            end = start + segment_size
            segment = audio[start:end]
            rms = np.sqrt(np.mean(segment ** 2))
            energy.append(float(rms))
        
        return energy
    
    def compute_zero_crossing_rate(self, audio: np.ndarray) -> float:
        """Compute zero crossing rate."""
        crossings = np.sum(np.abs(np.diff(np.signbit(audio))))
        return float(crossings / len(audio))
    
    def compute_spectral_centroid(
        self,
        audio: np.ndarray,
        sample_rate: int,
        frame_size: int = 2048
    ) -> float:
        """Compute mean spectral centroid."""
        centroids = []
        
        for i in range(0, len(audio) - frame_size, frame_size // 2):
            frame = audio[i:i + frame_size]
            
            # Compute FFT
            spectrum = np.abs(np.fft.rfft(frame * np.hanning(len(frame))))
            freqs = np.fft.rfftfreq(len(frame), 1 / sample_rate)
            
            if np.sum(spectrum) > 0:
                centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
                centroids.append(centroid)
        
        return float(np.mean(centroids)) if centroids else 0.0
    
    def analyze_audio(self, video_path: str) -> AudioFeatures:
        """
        Complete audio analysis from video file.
        
        Args:
            video_path: Path to video file
        
        Returns:
            AudioFeatures with analysis results
        """
        # Extract audio
        audio_path = self.extractor.extract_audio(video_path)
        
        if audio_path is None:
            return AudioFeatures(
                duration_seconds=0,
                sample_rate=0,
                pitch_mean=0,
                pitch_std=0,
                pitch_variance_score=50,
                jitter_mean=0,
                jitter_score=50,
                energy_profile=[],
                zero_crossing_rate=0,
                spectral_centroid_mean=0,
                is_valid=False,
                error_message="Failed to extract audio"
            )
        
        try:
            # Load audio data
            audio, sample_rate = self.extractor.load_audio_data(audio_path)
            
            if audio is None or len(audio) == 0:
                return AudioFeatures(
                    duration_seconds=0,
                    sample_rate=0,
                    pitch_mean=0,
                    pitch_std=0,
                    pitch_variance_score=50,
                    jitter_mean=0,
                    jitter_score=50,
                    energy_profile=[],
                    zero_crossing_rate=0,
                    spectral_centroid_mean=0,
                    is_valid=False,
                    error_message="Failed to load audio data"
                )
            
            duration = len(audio) / sample_rate
            
            # Compute features
            pitch_mean, pitch_std, pitch_score = self.compute_pitch_features(audio, sample_rate)
            jitter_mean, jitter_score = self.compute_jitter(audio, sample_rate)
            energy_profile = self.compute_energy_profile(audio)
            zcr = self.compute_zero_crossing_rate(audio)
            spectral_centroid = self.compute_spectral_centroid(audio, sample_rate)
            
            return AudioFeatures(
                duration_seconds=duration,
                sample_rate=sample_rate,
                pitch_mean=pitch_mean,
                pitch_std=pitch_std,
                pitch_variance_score=pitch_score,
                jitter_mean=jitter_mean,
                jitter_score=jitter_score,
                energy_profile=energy_profile,
                zero_crossing_rate=zcr,
                spectral_centroid_mean=spectral_centroid,
                is_valid=True
            )
        
        finally:
            # Cleanup temp file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass


class LipSyncAnalyzer:
    """Analyze lip-audio synchronization."""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def extract_mouth_region(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Extract mouth region from frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        
        # Approximate mouth region (lower third of face)
        mouth_y = y + int(h * 0.6)
        mouth_h = int(h * 0.3)
        mouth_x = x + int(w * 0.2)
        mouth_w = int(w * 0.6)
        
        mouth = gray[mouth_y:mouth_y + mouth_h, mouth_x:mouth_x + mouth_w]
        
        return mouth if mouth.size > 0 else None
    
    def compute_mouth_movement(self, frames: List[np.ndarray]) -> List[float]:
        """
        Compute mouth movement energy over frames.
        
        Args:
            frames: List of BGR video frames
        
        Returns:
            List of movement energy values
        """
        movements = []
        prev_mouth = None
        
        for frame in frames:
            mouth = self.extract_mouth_region(frame)
            
            if mouth is None:
                movements.append(0.0)
                continue
            
            # Resize for consistency
            mouth = cv2.resize(mouth, (64, 32))
            
            if prev_mouth is not None:
                # Compute frame difference
                diff = np.abs(mouth.astype(float) - prev_mouth.astype(float))
                energy = np.mean(diff)
                movements.append(float(energy))
            else:
                movements.append(0.0)
            
            prev_mouth = mouth
        
        return movements
    
    def analyze_sync(
        self,
        video_path: str,
        audio_energy: List[float],
        max_frames: int = 300
    ) -> LipSyncFeatures:
        """
        Analyze lip-audio synchronization.
        
        Args:
            video_path: Path to video file
            audio_energy: Audio energy profile
            max_frames: Maximum frames to analyze
        
        Returns:
            LipSyncFeatures with analysis results
        """
        # Extract video frames
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        frames = []
        while len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        
        if not frames:
            return LipSyncFeatures(
                mouth_movement_energy=[],
                audio_energy=audio_energy,
                correlation=0,
                sync_score=50,
                lag_frames=0,
                mismatch_regions=[]
            )
        
        # Compute mouth movement
        mouth_energy = self.compute_mouth_movement(frames)
        
        # Resample to match audio energy length
        if len(audio_energy) > 0 and len(mouth_energy) > 0:
            # Interpolate to same length
            target_len = min(len(audio_energy), len(mouth_energy))
            
            audio_resampled = np.interp(
                np.linspace(0, 1, target_len),
                np.linspace(0, 1, len(audio_energy)),
                audio_energy
            )
            
            mouth_resampled = np.interp(
                np.linspace(0, 1, target_len),
                np.linspace(0, 1, len(mouth_energy)),
                mouth_energy
            )
            
            # Normalize
            audio_norm = (audio_resampled - np.mean(audio_resampled)) / (np.std(audio_resampled) + 1e-6)
            mouth_norm = (mouth_resampled - np.mean(mouth_resampled)) / (np.std(mouth_resampled) + 1e-6)
            
            # Cross-correlation to find lag
            correlation = np.correlate(audio_norm, mouth_norm, mode='full')
            lag = np.argmax(correlation) - len(audio_norm) + 1
            max_corr = correlation[np.argmax(correlation)] / len(audio_norm)
            
            # Find mismatch regions (where correlation drops)
            window_size = max(1, target_len // 10)
            mismatch_regions = []
            
            for i in range(0, target_len - window_size, window_size // 2):
                window_a = audio_norm[i:i + window_size]
                window_m = mouth_norm[i:i + window_size]
                local_corr = np.corrcoef(window_a, window_m)[0, 1]
                
                if np.isnan(local_corr) or local_corr < 0.2:
                    # Convert to time
                    start_time = i / fps
                    end_time = (i + window_size) / fps
                    mismatch_regions.append((start_time, end_time))
        else:
            max_corr = 0
            lag = 0
            mismatch_regions = []
        
        # Sync score: based on correlation and lag
        if abs(lag) > fps * 0.5:  # More than 0.5s lag is suspicious
            lag_penalty = min(50, abs(lag) / fps * 50)
        else:
            lag_penalty = 0
        
        sync_score = max(0, max_corr * 100 - lag_penalty)
        
        return LipSyncFeatures(
            mouth_movement_energy=mouth_energy,
            audio_energy=audio_energy,
            correlation=float(max_corr),
            sync_score=float(np.clip(sync_score, 0, 100)),
            lag_frames=int(lag),
            mismatch_regions=mismatch_regions
        )


class AudioVideoAnalyzer:
    """
    Complete multi-modal audio-video analysis.
    
    Combines audio spoof detection with lip-sync analysis
    for comprehensive deepfake detection.
    """
    
    def __init__(self):
        self.audio_analyzer = AudioAnalyzer()
        self.lip_sync_analyzer = LipSyncAnalyzer()
    
    def analyze(self, video_path: str) -> MultiModalAnalysis:
        """
        Perform complete multi-modal analysis.
        
        Args:
            video_path: Path to video file
        
        Returns:
            MultiModalAnalysis with comprehensive results
        """
        # Analyze audio
        audio_features = self.audio_analyzer.analyze_audio(video_path)
        
        # Compute audio spoof score
        if audio_features.is_valid:
            audio_spoof_score = (
                audio_features.pitch_variance_score * 0.5 +
                audio_features.jitter_score * 0.5
            )
        else:
            audio_spoof_score = 50  # Neutral if no audio
        
        # Analyze lip sync
        lip_sync_features = None
        lip_sync_score = 50  # Neutral default
        
        if audio_features.is_valid and audio_features.energy_profile:
            lip_sync_features = self.lip_sync_analyzer.analyze_sync(
                video_path,
                audio_features.energy_profile
            )
            lip_sync_score = lip_sync_features.sync_score
        
        # Combined score (higher = more authentic)
        # Audio spoof: higher = more suspicious, so invert
        # Lip sync: higher = better sync
        combined_score = (
            (100 - audio_spoof_score) * 0.4 +
            lip_sync_score * 0.6
        )
        
        # Confidence based on data quality
        confidence = 80.0 if audio_features.is_valid else 30.0
        if lip_sync_features and len(lip_sync_features.mouth_movement_energy) > 50:
            confidence += 20.0
        
        details = {
            'audio_valid': audio_features.is_valid,
            'audio_duration': audio_features.duration_seconds,
            'pitch_analysis': {
                'mean': audio_features.pitch_mean,
                'std': audio_features.pitch_std,
                'score': audio_features.pitch_variance_score
            },
            'jitter_analysis': {
                'value': audio_features.jitter_mean,
                'score': audio_features.jitter_score
            },
            'lip_sync': {
                'correlation': lip_sync_features.correlation if lip_sync_features else 0,
                'lag_frames': lip_sync_features.lag_frames if lip_sync_features else 0,
                'mismatch_count': len(lip_sync_features.mismatch_regions) if lip_sync_features else 0
            }
        }
        
        return MultiModalAnalysis(
            audio_features=audio_features,
            lip_sync_features=lip_sync_features,
            audio_spoof_score=float(audio_spoof_score),
            lip_sync_score=float(lip_sync_score),
            combined_score=float(np.clip(combined_score, 0, 100)),
            confidence=float(min(confidence, 100)),
            analysis_details=details
        )
    
    def to_dict(self, analysis: MultiModalAnalysis) -> Dict[str, Any]:
        """Convert analysis to dictionary for JSON serialization."""
        result = {
            'audio_spoof_score': analysis.audio_spoof_score,
            'lip_sync_score': analysis.lip_sync_score,
            'combined_score': analysis.combined_score,
            'confidence': analysis.confidence,
            'audio_features': {
                'is_valid': analysis.audio_features.is_valid,
                'duration_seconds': analysis.audio_features.duration_seconds,
                'pitch_mean': analysis.audio_features.pitch_mean,
                'pitch_variance_score': analysis.audio_features.pitch_variance_score,
                'jitter_score': analysis.audio_features.jitter_score
            },
            'analysis_details': analysis.analysis_details
        }
        
        if analysis.lip_sync_features:
            result['lip_sync_features'] = {
                'correlation': analysis.lip_sync_features.correlation,
                'sync_score': analysis.lip_sync_features.sync_score,
                'lag_frames': analysis.lip_sync_features.lag_frames,
                'mismatch_regions': analysis.lip_sync_features.mismatch_regions
            }
        
        return result

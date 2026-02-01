"""
Explainability Pipeline Integration Module

Provides unified interface for all explainability features:
- Grad-CAM heatmaps
- Frame probability timeline
- Forensics analysis
- Multi-modal analysis
- Fake type classification
- Threat level scoring
- Ethics panel

This module is designed to be called from Django views without
putting business logic inside the views.

IMPORTANT: All analysis is ADDITIVE and does not modify existing inference.
"""

import torch
import numpy as np
import cv2
import os
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from .gradcam import GradCAMExplainer, generate_gradcam_heatmap, generate_sequence_gradcam
from .timeline import FrameProbabilityTimeline, extract_frame_probabilities_from_model
from .forensics import DeepfakeForensicsAnalyzer, ForensicsMetrics
from .multimodal import AudioVideoAnalyzer, MultiModalAnalysis
from .classifier import FakeTypeClassifier, FakeTypeResult, FakeType
from .threat_level import ThreatLevelScorer, ThreatAssessment, ThreatLevel
from .ethics import EthicsBiasPanel, EthicsPanel


@dataclass
class ExplainabilityResult:
    """Complete explainability analysis result."""
    # Core detection (from existing model - not modified)
    prediction_label: str
    prediction_confidence: float
    
    # Grad-CAM (Feature 1)
    gradcam_images: List[str]  # Paths to heatmap images
    gradcam_summary: Dict[str, Any]
    
    # Timeline (Feature 2)
    timeline_data: Dict[str, Any]  # Chart.js compatible
    timeline_stats: Dict[str, float]
    
    # Forensics (Feature 3)
    forensics_metrics: Dict[str, Any]
    forensics_summary: str
    
    # Multi-modal (Feature 5)
    multimodal_analysis: Dict[str, Any]
    audio_video_score: float
    
    # Fake Type (Feature 6)
    fake_type: str
    fake_type_confidence: float
    fake_type_explanation: str
    
    # Threat Level (Feature 7)
    threat_level: str
    threat_score: float
    threat_explanation: str
    threat_recommendations: List[str]
    threat_color: str
    
    # Ethics (Feature 8)
    ethics_summary: str
    
    # Metadata
    analysis_timestamp: str
    analysis_duration_ms: float
    video_info: Dict[str, Any]


class ExplainabilityPipeline:
    """
    Unified pipeline for all explainability features.
    
    Designed to run AFTER existing model inference without modifying it.
    All features are optional and can be enabled/disabled.
    """
    
    def __init__(
        self,
        model: Optional[torch.nn.Module] = None,
        transform: Optional[callable] = None,
        device: str = 'cpu',
        output_dir: str = './explainability_output'
    ):
        """
        Initialize explainability pipeline.
        
        Args:
            model: Loaded deepfake detection model (for Grad-CAM)
            transform: Frame preprocessing transform
            device: Computation device
            output_dir: Directory for output files
        """
        self.model = model
        self.transform = transform
        self.device = device
        self.output_dir = output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize analyzers
        self.forensics_analyzer = DeepfakeForensicsAnalyzer()
        self.multimodal_analyzer = AudioVideoAnalyzer()
        self.fake_classifier = FakeTypeClassifier()
        self.threat_scorer = ThreatLevelScorer()
        self.ethics_panel = EthicsBiasPanel()
    
    def analyze_video(
        self,
        video_path: str,
        model_prediction: Dict[str, Any],
        input_tensor: Optional[torch.Tensor] = None,
        frames: Optional[List[np.ndarray]] = None,
        enable_gradcam: bool = True,
        enable_timeline: bool = True,
        enable_forensics: bool = True,
        enable_multimodal: bool = True,
        enable_classification: bool = True,
        enable_threat: bool = True,
        max_frames: int = 100,
        video_name: str = "video"
    ) -> ExplainabilityResult:
        """
        Run complete explainability analysis on a video.
        
        Args:
            video_path: Path to video file
            model_prediction: Existing model prediction (dict with 'prediction_label', 'confidence')
            input_tensor: Model input tensor (for Grad-CAM and timeline)
            frames: Original video frames (for Grad-CAM overlay)
            enable_*: Feature flags
            max_frames: Maximum frames to analyze
            video_name: Base name for output files
        
        Returns:
            ExplainabilityResult with all analysis
        """
        import time
        start_time = time.time()
        
        # Initialize result containers
        gradcam_images = []
        gradcam_summary = {}
        timeline_data = {'labels': [], 'datasets': []}
        timeline_stats = {}
        forensics_dict = {}
        forensics_summary = ""
        multimodal_dict = {}
        audio_video_score = 50.0
        fake_type_str = "unknown"
        fake_type_confidence = 0.0
        fake_type_explanation = ""
        threat_level_str = "unknown"
        threat_score = 50.0
        threat_explanation = ""
        threat_recommendations = []
        threat_color = "#6c757d"
        
        # Get video info
        video_info = self._get_video_info(video_path)
        fps = video_info.get('fps', 30.0)
        
        # Load frames if not provided
        if frames is None and (enable_gradcam or enable_forensics):
            frames = self._load_video_frames(video_path, max_frames)
        
        # Feature 1: Grad-CAM
        if enable_gradcam and self.model is not None and input_tensor is not None and frames:
            try:
                gradcam_output_dir = os.path.join(self.output_dir, 'gradcam')
                os.makedirs(gradcam_output_dir, exist_ok=True)
                
                results = generate_sequence_gradcam(
                    self.model, input_tensor, frames[:min(len(frames), input_tensor.shape[1])],
                    gradcam_output_dir, video_name
                )
                
                gradcam_images = [r['save_path'] for r in results if r.get('save_path')]
                gradcam_summary = {
                    'frames_processed': len(results),
                    'average_confidence': np.mean([r['confidence'] for r in results]) if results else 0
                }
            except Exception as e:
                gradcam_summary = {'error': str(e)}
        
        # Feature 2: Timeline
        if enable_timeline and self.model is not None and input_tensor is not None:
            try:
                timeline = extract_frame_probabilities_from_model(
                    self.model, input_tensor, fps
                )
                timeline_data = timeline.to_chartjs_data()
                timeline_stats = timeline.get_temporal_stats()
            except Exception as e:
                timeline_stats = {'error': str(e)}
        
        # Feature 3: Forensics
        if enable_forensics:
            try:
                if frames:
                    metrics = self.forensics_analyzer.analyze_frames(frames[:max_frames])
                else:
                    metrics = self.forensics_analyzer.analyze_video(video_path, max_frames)
                
                forensics_dict = asdict(metrics)
                forensics_summary = self._generate_forensics_summary(metrics)
            except Exception as e:
                forensics_dict = {'error': str(e)}
                forensics_summary = f"Forensics analysis failed: {str(e)}"
        
        # Feature 5: Multi-modal
        if enable_multimodal:
            try:
                multimodal_result = self.multimodal_analyzer.analyze(video_path)
                multimodal_dict = self.multimodal_analyzer.to_dict(multimodal_result)
                audio_video_score = multimodal_result.combined_score
            except Exception as e:
                multimodal_dict = {'error': str(e)}
        
        # Feature 6: Fake Type Classification
        if enable_classification:
            try:
                classification_result = self.fake_classifier.classify(
                    model_prediction=model_prediction,
                    forensics_metrics=forensics_dict if forensics_dict else None,
                    multimodal_metrics=multimodal_dict if multimodal_dict else None,
                    timeline_stats=timeline_stats if timeline_stats else None
                )
                fake_type_str = classification_result.primary_type.value
                fake_type_confidence = classification_result.confidence
                fake_type_explanation = classification_result.explanation
            except Exception as e:
                fake_type_explanation = f"Classification failed: {str(e)}"
        
        # Feature 7: Threat Level
        if enable_threat:
            try:
                fake_type_dict = {
                    'type': fake_type_str,
                    'confidence': fake_type_confidence
                } if enable_classification else None
                
                threat_result = self.threat_scorer.assess(
                    model_prediction=model_prediction,
                    forensics_metrics=forensics_dict if forensics_dict else None,
                    multimodal_metrics=multimodal_dict if multimodal_dict else None,
                    timeline_stats=timeline_stats if timeline_stats else None,
                    fake_type_result=fake_type_dict
                )
                threat_level_str = threat_result.level.value
                threat_score = threat_result.overall_score
                threat_explanation = threat_result.explanation
                threat_recommendations = threat_result.recommendations
                threat_color = threat_result.color_code
            except Exception as e:
                threat_explanation = f"Threat assessment failed: {str(e)}"
        
        # Feature 8: Ethics summary
        ethics_summary = self.ethics_panel.generate_summary()
        
        # Calculate duration
        analysis_duration = (time.time() - start_time) * 1000
        
        return ExplainabilityResult(
            prediction_label=model_prediction.get('prediction_label', 'UNKNOWN'),
            prediction_confidence=model_prediction.get('confidence', 0),
            gradcam_images=gradcam_images,
            gradcam_summary=gradcam_summary,
            timeline_data=timeline_data,
            timeline_stats=timeline_stats,
            forensics_metrics=forensics_dict,
            forensics_summary=forensics_summary,
            multimodal_analysis=multimodal_dict,
            audio_video_score=audio_video_score,
            fake_type=fake_type_str,
            fake_type_confidence=fake_type_confidence,
            fake_type_explanation=fake_type_explanation,
            threat_level=threat_level_str,
            threat_score=threat_score,
            threat_explanation=threat_explanation,
            threat_recommendations=threat_recommendations,
            threat_color=threat_color,
            ethics_summary=ethics_summary,
            analysis_timestamp=datetime.now().isoformat(),
            analysis_duration_ms=analysis_duration,
            video_info=video_info
        )
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata."""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {'error': 'Cannot open video'}
        
        info = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration_seconds': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
                               if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
        }
        
        cap.release()
        return info
    
    def _load_video_frames(self, video_path: str, max_frames: int) -> List[np.ndarray]:
        """Load frames from video file."""
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        return frames
    
    def _generate_forensics_summary(self, metrics: ForensicsMetrics) -> str:
        """Generate human-readable forensics summary."""
        summary_parts = []
        
        # Face consistency
        if metrics.face_consistency_score < 60:
            summary_parts.append(f"⚠️ Low face consistency ({metrics.face_consistency_score:.1f}%)")
        else:
            summary_parts.append(f"✓ Face consistency: {metrics.face_consistency_score:.1f}%")
        
        # Eye blink
        if metrics.eye_blink_score < 40:
            summary_parts.append(f"⚠️ Abnormal blink pattern ({metrics.eye_blink_score:.1f}%)")
        else:
            summary_parts.append(f"✓ Blink pattern: {metrics.eye_blink_score:.1f}%")
        
        # Temporal stability
        if metrics.temporal_stability_score < 50:
            summary_parts.append(f"⚠️ Low temporal stability ({metrics.temporal_stability_score:.1f}%)")
        else:
            summary_parts.append(f"✓ Temporal stability: {metrics.temporal_stability_score:.1f}%")
        
        # Artifacts
        if metrics.compression_artifact_score > 60:
            summary_parts.append(f"⚠️ High artifacts ({metrics.compression_artifact_score:.1f}%)")
        
        # Overall
        summary_parts.append(f"📊 Overall forensics score: {metrics.overall_forensics_score:.1f}%")
        
        return "\n".join(summary_parts)
    
    def to_dict(self, result: ExplainabilityResult) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return asdict(result)
    
    def to_json(self, result: ExplainabilityResult, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(result), indent=indent, default=str)
    
    def get_ethics_panel(self) -> Dict[str, Any]:
        """Get full ethics panel data."""
        panel = self.ethics_panel.generate_panel()
        return self.ethics_panel.to_dict(panel)
    
    def get_ethics_html(self) -> str:
        """Get ethics panel as HTML."""
        return self.ethics_panel.generate_html_panel()


def create_explainability_pipeline(
    model: torch.nn.Module,
    transform: callable,
    output_dir: str
) -> ExplainabilityPipeline:
    """
    Factory function to create explainability pipeline.
    
    Args:
        model: Loaded deepfake detection model
        transform: Frame preprocessing transform
        output_dir: Output directory for analysis files
    
    Returns:
        Configured ExplainabilityPipeline
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.eval()
    
    return ExplainabilityPipeline(
        model=model,
        transform=transform,
        device=device,
        output_dir=output_dir
    )


# Convenience functions for individual features

def run_gradcam_analysis(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    frames: List[np.ndarray],
    output_dir: str,
    video_name: str = "video"
) -> List[Dict[str, Any]]:
    """Run Grad-CAM analysis standalone."""
    return generate_sequence_gradcam(model, input_tensor, frames, output_dir, video_name)


def run_forensics_analysis(
    video_path: str,
    max_frames: int = 100
) -> Dict[str, Any]:
    """Run forensics analysis standalone."""
    analyzer = DeepfakeForensicsAnalyzer()
    metrics = analyzer.analyze_video(video_path, max_frames)
    return asdict(metrics)


def run_multimodal_analysis(video_path: str) -> Dict[str, Any]:
    """Run multi-modal analysis standalone."""
    analyzer = AudioVideoAnalyzer()
    result = analyzer.analyze(video_path)
    return analyzer.to_dict(result)


def run_threat_assessment(
    model_prediction: Dict[str, Any],
    forensics: Optional[Dict[str, Any]] = None,
    multimodal: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run threat assessment standalone."""
    scorer = ThreatLevelScorer()
    result = scorer.assess(model_prediction, forensics, multimodal)
    return scorer.to_dict(result)

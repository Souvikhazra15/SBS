"""
Explainability and Forensics Module for Deepfake Detection System

This module provides additive, modular components for:
- Grad-CAM visual explanations
- Frame-wise probability timeline
- Deepfake forensics analysis
- Real-time webcam detection
- Multi-modal audio-video analysis
- Fake type classification
- Threat level scoring
- Ethics and bias panel

IMPORTANT: This module is strictly ADDITIVE and does NOT modify any existing
model, inference logic, or decision engine.
"""

from .gradcam import GradCAMExplainer, generate_gradcam_heatmap
from .timeline import FrameProbabilityTimeline
from .forensics import DeepfakeForensicsAnalyzer
from .webcam import WebcamDeepfakeDetector
from .multimodal import AudioVideoAnalyzer
from .classifier import FakeTypeClassifier
from .threat_level import ThreatLevelScorer
from .ethics import EthicsBiasPanel
from .integration import ExplainabilityPipeline

__all__ = [
    'GradCAMExplainer',
    'generate_gradcam_heatmap',
    'FrameProbabilityTimeline',
    'DeepfakeForensicsAnalyzer',
    'WebcamDeepfakeDetector',
    'AudioVideoAnalyzer',
    'FakeTypeClassifier',
    'ThreatLevelScorer',
    'EthicsBiasPanel',
    'ExplainabilityPipeline',
]

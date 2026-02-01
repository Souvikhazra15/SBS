"""
Fake Type Classification Module

Classifies deepfakes beyond detection:
- GAN-based face swap
- Lip-sync manipulation
- Face reenactment

Uses rule-based approach with existing forensics signals.
No retraining required.

IMPORTANT: This is purely additive and rule-based.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FakeType(Enum):
    """Types of deepfake manipulation."""
    AUTHENTIC = "authentic"
    GAN_FACE_SWAP = "gan_face_swap"
    LIP_SYNC = "lip_sync_manipulation"
    FACE_REENACTMENT = "face_reenactment"
    UNKNOWN_MANIPULATION = "unknown_manipulation"


@dataclass
class FakeTypeResult:
    """Fake type classification result."""
    primary_type: FakeType
    confidence: float  # 0-100
    all_scores: Dict[str, float]
    evidence: List[str]
    explanation: str


class FakeTypeClassifier:
    """
    Rule-based fake type classifier.
    
    Uses forensics metrics and analysis results to classify
    the type of deepfake manipulation without additional training.
    """
    
    # Thresholds for classification
    THRESHOLDS = {
        'face_swap_face_consistency': 60,  # Low consistency suggests face swap
        'face_swap_temporal_stability': 55,  # Low stability in swap regions
        'lip_sync_audio_mismatch': 40,  # Poor audio-lip sync
        'lip_sync_mouth_stability': 45,  # Mouth region instability
        'reenactment_expression_variance': 0.7,  # High expression change rate
        'reenactment_pose_variance': 0.5,  # High pose change
        'artifact_threshold': 50,  # Compression artifact level
    }
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize classifier.
        
        Args:
            thresholds: Optional custom thresholds
        """
        self.thresholds = {**self.THRESHOLDS}
        if thresholds:
            self.thresholds.update(thresholds)
    
    def classify(
        self,
        model_prediction: Dict[str, Any],
        forensics_metrics: Optional[Dict[str, Any]] = None,
        multimodal_metrics: Optional[Dict[str, Any]] = None,
        timeline_stats: Optional[Dict[str, Any]] = None
    ) -> FakeTypeResult:
        """
        Classify the type of fake based on available metrics.
        
        Args:
            model_prediction: Model prediction with confidence
            forensics_metrics: Forensics analysis results
            multimodal_metrics: Audio-video analysis results
            timeline_stats: Frame probability timeline statistics
        
        Returns:
            FakeTypeResult with classification
        """
        # Initialize scores for each type
        scores = {
            FakeType.AUTHENTIC: 0.0,
            FakeType.GAN_FACE_SWAP: 0.0,
            FakeType.LIP_SYNC: 0.0,
            FakeType.FACE_REENACTMENT: 0.0,
            FakeType.UNKNOWN_MANIPULATION: 0.0
        }
        
        evidence = []
        
        # Check if model predicts real
        if model_prediction.get('prediction_label') == 'REAL':
            model_confidence = model_prediction.get('confidence', 0)
            if model_confidence > 70:
                scores[FakeType.AUTHENTIC] += 50
                evidence.append(f"Model predicts REAL with {model_confidence:.1f}% confidence")
        else:
            fake_confidence = model_prediction.get('confidence', 0)
            evidence.append(f"Model predicts FAKE with {fake_confidence:.1f}% confidence")
        
        # Analyze forensics metrics
        if forensics_metrics:
            self._analyze_forensics(forensics_metrics, scores, evidence)
        
        # Analyze multimodal metrics
        if multimodal_metrics:
            self._analyze_multimodal(multimodal_metrics, scores, evidence)
        
        # Analyze timeline for temporal patterns
        if timeline_stats:
            self._analyze_timeline(timeline_stats, scores, evidence)
        
        # Determine primary type
        primary_type, confidence = self._determine_primary_type(scores, model_prediction)
        
        # Generate explanation
        explanation = self._generate_explanation(primary_type, evidence, scores)
        
        # Convert scores to percentages
        score_percentages = {t.value: float(s) for t, s in scores.items()}
        
        return FakeTypeResult(
            primary_type=primary_type,
            confidence=confidence,
            all_scores=score_percentages,
            evidence=evidence,
            explanation=explanation
        )
    
    def _analyze_forensics(
        self,
        metrics: Dict[str, Any],
        scores: Dict[FakeType, float],
        evidence: List[str]
    ) -> None:
        """Analyze forensics metrics for classification."""
        
        # Face consistency analysis
        face_score = metrics.get('face_consistency_score', 100)
        if face_score < self.thresholds['face_swap_face_consistency']:
            scores[FakeType.GAN_FACE_SWAP] += 25
            evidence.append(f"Low face consistency: {face_score:.1f}%")
        else:
            scores[FakeType.AUTHENTIC] += 15
        
        # Temporal stability
        stability_score = metrics.get('temporal_stability_score', 100)
        if stability_score < self.thresholds['face_swap_temporal_stability']:
            scores[FakeType.GAN_FACE_SWAP] += 15
            scores[FakeType.FACE_REENACTMENT] += 10
            evidence.append(f"Low temporal stability: {stability_score:.1f}%")
        
        # Eye blink analysis
        blink_score = metrics.get('eye_blink_score', 50)
        if blink_score < 30:
            scores[FakeType.GAN_FACE_SWAP] += 20
            scores[FakeType.FACE_REENACTMENT] += 15
            evidence.append(f"Abnormal blink pattern: {blink_score:.1f}%")
        
        # Compression artifacts
        artifact_score = metrics.get('compression_artifact_score', 0)
        if artifact_score > self.thresholds['artifact_threshold']:
            scores[FakeType.GAN_FACE_SWAP] += 10
            scores[FakeType.UNKNOWN_MANIPULATION] += 5
            evidence.append(f"High compression artifacts: {artifact_score:.1f}%")
    
    def _analyze_multimodal(
        self,
        metrics: Dict[str, Any],
        scores: Dict[FakeType, float],
        evidence: List[str]
    ) -> None:
        """Analyze multimodal metrics for classification."""
        
        # Lip sync score
        lip_sync_score = metrics.get('lip_sync_score', 100)
        if lip_sync_score < self.thresholds['lip_sync_audio_mismatch']:
            scores[FakeType.LIP_SYNC] += 35
            evidence.append(f"Poor lip-audio sync: {lip_sync_score:.1f}%")
        
        # Audio spoof indicators
        audio_spoof = metrics.get('audio_spoof_score', 0)
        if audio_spoof > 60:
            scores[FakeType.LIP_SYNC] += 20
            evidence.append(f"Audio spoofing indicators: {audio_spoof:.1f}%")
        
        # Lip sync correlation
        if 'lip_sync_features' in metrics:
            correlation = metrics['lip_sync_features'].get('correlation', 1)
            if correlation < 0.3:
                scores[FakeType.LIP_SYNC] += 25
                evidence.append(f"Low audio-visual correlation: {correlation:.2f}")
    
    def _analyze_timeline(
        self,
        stats: Dict[str, Any],
        scores: Dict[FakeType, float],
        evidence: List[str]
    ) -> None:
        """Analyze probability timeline for patterns."""
        
        # Temporal variance
        variance = stats.get('temporal_variance', 0)
        if variance > 0.15:
            scores[FakeType.FACE_REENACTMENT] += 15
            evidence.append(f"High temporal probability variance: {variance:.3f}")
        
        # Anomaly ratio
        anomaly_ratio = stats.get('anomaly_ratio', 0)
        if anomaly_ratio > 0.2:
            scores[FakeType.GAN_FACE_SWAP] += 10
            scores[FakeType.FACE_REENACTMENT] += 10
            evidence.append(f"High anomaly ratio: {anomaly_ratio:.1%}")
        
        # Mean probability analysis
        mean_prob = stats.get('mean_fake_probability', 0)
        if mean_prob > 0.8:
            scores[FakeType.GAN_FACE_SWAP] += 10
            evidence.append(f"Consistently high fake probability: {mean_prob:.1%}")
    
    def _determine_primary_type(
        self,
        scores: Dict[FakeType, float],
        model_prediction: Dict[str, Any]
    ) -> Tuple[FakeType, float]:
        """Determine primary fake type from scores."""
        
        # If model predicts real and authentic score is high
        if model_prediction.get('prediction_label') == 'REAL':
            model_conf = model_prediction.get('confidence', 0)
            if model_conf > 70 and scores[FakeType.AUTHENTIC] > 40:
                return FakeType.AUTHENTIC, min(95, model_conf)
        
        # Find highest scoring fake type
        fake_types = {k: v for k, v in scores.items() if k != FakeType.AUTHENTIC}
        
        if not fake_types or all(v == 0 for v in fake_types.values()):
            # No clear indicators, use unknown
            return FakeType.UNKNOWN_MANIPULATION, 40.0
        
        max_type = max(fake_types, key=fake_types.get)
        max_score = fake_types[max_type]
        
        # Normalize confidence
        total_score = sum(fake_types.values())
        if total_score > 0:
            confidence = (max_score / total_score) * 100
        else:
            confidence = 40.0
        
        # Apply minimum thresholds
        if max_score < 20:
            return FakeType.UNKNOWN_MANIPULATION, min(50, confidence)
        
        return max_type, min(95, confidence)
    
    def _generate_explanation(
        self,
        fake_type: FakeType,
        evidence: List[str],
        scores: Dict[FakeType, float]
    ) -> str:
        """Generate human-readable explanation."""
        
        explanations = {
            FakeType.AUTHENTIC: 
                "Analysis indicates this video is likely authentic. "
                "Face consistency, temporal stability, and audio-visual sync "
                "are within normal parameters.",
            
            FakeType.GAN_FACE_SWAP:
                "This video shows signs of GAN-based face swap manipulation. "
                "Indicators include inconsistent face features across frames, "
                "unnatural blink patterns, and potential compression artifacts "
                "around facial boundaries.",
            
            FakeType.LIP_SYNC:
                "This video appears to be a lip-sync manipulation (audio deepfake). "
                "The audio track shows signs of synthesis or modification, "
                "and the lip movements do not properly correlate with the audio.",
            
            FakeType.FACE_REENACTMENT:
                "This video shows signs of face reenactment manipulation. "
                "The facial expressions and movements appear to be transferred "
                "from another source, with temporal inconsistencies and "
                "unnatural expression transitions.",
            
            FakeType.UNKNOWN_MANIPULATION:
                "This video shows signs of manipulation, but the specific type "
                "could not be determined with high confidence. Further manual "
                "analysis is recommended."
        }
        
        base_explanation = explanations.get(fake_type, explanations[FakeType.UNKNOWN_MANIPULATION])
        
        if evidence:
            evidence_str = " Key indicators: " + "; ".join(evidence[:3]) + "."
            return base_explanation + evidence_str
        
        return base_explanation
    
    def get_classification_report(self, result: FakeTypeResult) -> Dict[str, Any]:
        """Generate detailed classification report."""
        return {
            'classification': {
                'type': result.primary_type.value,
                'type_display': result.primary_type.value.replace('_', ' ').title(),
                'confidence': result.confidence
            },
            'all_type_scores': result.all_scores,
            'evidence': result.evidence,
            'explanation': result.explanation,
            'recommendations': self._get_recommendations(result.primary_type)
        }
    
    def _get_recommendations(self, fake_type: FakeType) -> List[str]:
        """Get recommendations based on fake type."""
        
        recommendations = {
            FakeType.AUTHENTIC: [
                "Video appears authentic based on automated analysis",
                "Manual verification recommended for high-stakes decisions",
                "Check video metadata and chain of custody"
            ],
            FakeType.GAN_FACE_SWAP: [
                "Compare with known authentic footage of the subject",
                "Examine face boundaries and hairline carefully",
                "Check for inconsistent lighting on face vs. background",
                "Look for artifacts around ears and facial contours"
            ],
            FakeType.LIP_SYNC: [
                "Compare audio with known samples of the speaker",
                "Look for timing mismatches between words and mouth movements",
                "Check for unnatural pauses or breathing patterns",
                "Examine if jaw movement matches speech intensity"
            ],
            FakeType.FACE_REENACTMENT: [
                "Look for unnatural or exaggerated expressions",
                "Check if head movements match body language",
                "Examine expression transitions for smoothness",
                "Compare with subject's typical expression patterns"
            ],
            FakeType.UNKNOWN_MANIPULATION: [
                "Request professional forensic analysis",
                "Gather additional reference footage for comparison",
                "Check video metadata and encoding history",
                "Consider multiple analysis tools for verification"
            ]
        }
        
        return recommendations.get(fake_type, recommendations[FakeType.UNKNOWN_MANIPULATION])

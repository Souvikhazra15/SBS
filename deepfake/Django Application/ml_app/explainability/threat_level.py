"""
Threat Level Scoring Module

SOC-style decision abstraction for deepfake detection.
Combines model confidence, forensics metrics, and audio scores
into actionable threat levels.

Levels:
- Safe: Low probability of manipulation
- Suspicious: Requires further investigation
- High Risk: Strong indicators of manipulation

IMPORTANT: Configurable thresholds, explainable scoring.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    """Threat level categories."""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ThreatAssessment:
    """Complete threat assessment result."""
    level: ThreatLevel
    level_display: str
    overall_score: float  # 0-100 (higher = more threat)
    confidence: float  # 0-100
    component_scores: Dict[str, float]
    risk_factors: List[str]
    mitigating_factors: List[str]
    explanation: str
    recommendations: List[str]
    color_code: str  # For UI display


class ThreatLevelScorer:
    """
    Comprehensive threat level scoring system.
    
    Combines multiple signals into a unified threat assessment
    with clear explanations for each decision.
    """
    
    DEFAULT_THRESHOLDS = {
        'safe_max': 25,           # Below this = Safe
        'suspicious_max': 55,     # Below this = Suspicious
        'high_risk_max': 80,      # Below this = High Risk
        # Above high_risk_max = Critical
    }
    
    DEFAULT_WEIGHTS = {
        'model_confidence': 0.35,
        'forensics_score': 0.25,
        'audio_score': 0.15,
        'temporal_score': 0.15,
        'fake_type_score': 0.10
    }
    
    COLOR_CODES = {
        ThreatLevel.SAFE: '#28a745',        # Green
        ThreatLevel.SUSPICIOUS: '#ffc107',  # Yellow
        ThreatLevel.HIGH_RISK: '#fd7e14',   # Orange
        ThreatLevel.CRITICAL: '#dc3545',    # Red
        ThreatLevel.UNKNOWN: '#6c757d'      # Gray
    }
    
    LEVEL_DISPLAY = {
        ThreatLevel.SAFE: 'Safe',
        ThreatLevel.SUSPICIOUS: 'Suspicious',
        ThreatLevel.HIGH_RISK: 'High Risk',
        ThreatLevel.CRITICAL: 'Critical',
        ThreatLevel.UNKNOWN: 'Unknown'
    }
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize threat scorer.
        
        Args:
            thresholds: Custom threat level thresholds
            weights: Custom component weights
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS}
        if thresholds:
            self.thresholds.update(thresholds)
        
        self.weights = {**self.DEFAULT_WEIGHTS}
        if weights:
            self.weights.update(weights)
            # Normalize weights
            total = sum(self.weights.values())
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def assess(
        self,
        model_prediction: Dict[str, Any],
        forensics_metrics: Optional[Dict[str, Any]] = None,
        multimodal_metrics: Optional[Dict[str, Any]] = None,
        timeline_stats: Optional[Dict[str, Any]] = None,
        fake_type_result: Optional[Dict[str, Any]] = None
    ) -> ThreatAssessment:
        """
        Perform comprehensive threat assessment.
        
        Args:
            model_prediction: Model prediction with confidence
            forensics_metrics: Forensics analysis results
            multimodal_metrics: Audio-video analysis results
            timeline_stats: Frame probability timeline statistics
            fake_type_result: Fake type classification result
        
        Returns:
            ThreatAssessment with complete analysis
        """
        component_scores = {}
        risk_factors = []
        mitigating_factors = []
        
        # 1. Model Confidence Score
        model_score, model_risks, model_mitigations = self._score_model_prediction(
            model_prediction
        )
        component_scores['model_confidence'] = model_score
        risk_factors.extend(model_risks)
        mitigating_factors.extend(model_mitigations)
        
        # 2. Forensics Score
        forensics_score, forensics_risks, forensics_mitigations = self._score_forensics(
            forensics_metrics
        )
        component_scores['forensics_score'] = forensics_score
        risk_factors.extend(forensics_risks)
        mitigating_factors.extend(forensics_mitigations)
        
        # 3. Audio/Multimodal Score
        audio_score, audio_risks, audio_mitigations = self._score_multimodal(
            multimodal_metrics
        )
        component_scores['audio_score'] = audio_score
        risk_factors.extend(audio_risks)
        mitigating_factors.extend(audio_mitigations)
        
        # 4. Temporal Score
        temporal_score, temporal_risks, temporal_mitigations = self._score_temporal(
            timeline_stats
        )
        component_scores['temporal_score'] = temporal_score
        risk_factors.extend(temporal_risks)
        mitigating_factors.extend(temporal_mitigations)
        
        # 5. Fake Type Score
        type_score, type_risks, type_mitigations = self._score_fake_type(
            fake_type_result
        )
        component_scores['fake_type_score'] = type_score
        risk_factors.extend(type_risks)
        mitigating_factors.extend(type_mitigations)
        
        # Calculate weighted overall score
        overall_score = sum(
            component_scores[k] * self.weights[k]
            for k in self.weights.keys()
        )
        
        # Determine threat level
        level = self._determine_level(overall_score)
        
        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(
            forensics_metrics,
            multimodal_metrics,
            timeline_stats
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            level, overall_score, component_scores, risk_factors
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(level, risk_factors)
        
        return ThreatAssessment(
            level=level,
            level_display=self.LEVEL_DISPLAY[level],
            overall_score=float(overall_score),
            confidence=float(confidence),
            component_scores=component_scores,
            risk_factors=risk_factors,
            mitigating_factors=mitigating_factors,
            explanation=explanation,
            recommendations=recommendations,
            color_code=self.COLOR_CODES[level]
        )
    
    def _score_model_prediction(
        self,
        prediction: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Score model prediction component."""
        risks = []
        mitigations = []
        
        label = prediction.get('prediction_label', 'UNKNOWN')
        confidence = prediction.get('confidence', 50)
        
        if label == 'FAKE':
            # Higher confidence in FAKE = higher threat score
            score = confidence
            if confidence > 80:
                risks.append(f"Model detects FAKE with high confidence ({confidence:.1f}%)")
            elif confidence > 60:
                risks.append(f"Model detects FAKE with moderate confidence ({confidence:.1f}%)")
        elif label == 'REAL':
            # Higher confidence in REAL = lower threat score
            score = 100 - confidence
            if confidence > 80:
                mitigations.append(f"Model detects REAL with high confidence ({confidence:.1f}%)")
        else:
            score = 50  # Unknown
        
        return float(score), risks, mitigations
    
    def _score_forensics(
        self,
        metrics: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score forensics analysis component."""
        if metrics is None:
            return 50.0, [], []
        
        risks = []
        mitigations = []
        
        # Get individual scores (higher forensics score = more authentic = lower threat)
        face_score = metrics.get('face_consistency_score', 50)
        blink_score = metrics.get('eye_blink_score', 50)
        stability_score = metrics.get('temporal_stability_score', 50)
        artifact_score = metrics.get('compression_artifact_score', 50)
        overall_forensics = metrics.get('overall_forensics_score', 50)
        
        # Convert to threat score (invert authenticity scores)
        threat_score = 100 - overall_forensics
        
        # Analyze individual components
        if face_score < 50:
            risks.append(f"Low face consistency score ({face_score:.1f}%)")
        elif face_score > 80:
            mitigations.append(f"High face consistency ({face_score:.1f}%)")
        
        if blink_score < 40:
            risks.append(f"Abnormal eye blink pattern ({blink_score:.1f}%)")
        
        if stability_score < 50:
            risks.append(f"Low temporal stability ({stability_score:.1f}%)")
        elif stability_score > 80:
            mitigations.append(f"Good temporal stability ({stability_score:.1f}%)")
        
        if artifact_score > 60:
            risks.append(f"High compression artifacts ({artifact_score:.1f}%)")
        
        return float(threat_score), risks, mitigations
    
    def _score_multimodal(
        self,
        metrics: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score audio-video analysis component."""
        if metrics is None:
            return 50.0, [], []
        
        risks = []
        mitigations = []
        
        audio_spoof = metrics.get('audio_spoof_score', 50)
        lip_sync = metrics.get('lip_sync_score', 50)
        combined = metrics.get('combined_score', 50)
        
        # Higher combined score = more authentic = lower threat
        threat_score = 100 - combined
        
        if lip_sync < 40:
            risks.append(f"Poor lip-audio synchronization ({lip_sync:.1f}%)")
        elif lip_sync > 70:
            mitigations.append(f"Good lip-audio sync ({lip_sync:.1f}%)")
        
        if audio_spoof > 60:
            risks.append(f"Audio spoofing indicators detected ({audio_spoof:.1f}%)")
        
        return float(threat_score), risks, mitigations
    
    def _score_temporal(
        self,
        stats: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score temporal analysis component."""
        if stats is None:
            return 50.0, [], []
        
        risks = []
        mitigations = []
        
        mean_fake_prob = stats.get('mean_fake_probability', 0.5)
        temporal_variance = stats.get('temporal_variance', 0)
        anomaly_ratio = stats.get('anomaly_ratio', 0)
        consistency = stats.get('temporal_consistency_score', 50)
        
        # Threat score based on fake probability and consistency
        threat_score = mean_fake_prob * 100 * 0.6 + (100 - consistency) * 0.4
        
        if mean_fake_prob > 0.7:
            risks.append(f"High average fake probability ({mean_fake_prob:.1%})")
        
        if anomaly_ratio > 0.2:
            risks.append(f"High temporal anomaly rate ({anomaly_ratio:.1%})")
        
        if consistency > 80:
            mitigations.append(f"High temporal consistency ({consistency:.1f}%)")
        
        return float(threat_score), risks, mitigations
    
    def _score_fake_type(
        self,
        result: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score fake type classification component."""
        if result is None:
            return 50.0, [], []
        
        risks = []
        mitigations = []
        
        fake_type = result.get('type', 'unknown')
        confidence = result.get('confidence', 50)
        
        if fake_type == 'authentic':
            threat_score = max(0, 100 - confidence)
            if confidence > 70:
                mitigations.append(f"Classified as authentic ({confidence:.1f}% confidence)")
        elif fake_type in ['gan_face_swap', 'lip_sync_manipulation', 'face_reenactment']:
            threat_score = confidence
            display_type = fake_type.replace('_', ' ').title()
            if confidence > 60:
                risks.append(f"Classified as {display_type} ({confidence:.1f}% confidence)")
        else:
            threat_score = 50
            risks.append("Unable to determine manipulation type with confidence")
        
        return float(threat_score), risks, mitigations
    
    def _determine_level(self, score: float) -> ThreatLevel:
        """Determine threat level from score."""
        if score <= self.thresholds['safe_max']:
            return ThreatLevel.SAFE
        elif score <= self.thresholds['suspicious_max']:
            return ThreatLevel.SUSPICIOUS
        elif score <= self.thresholds['high_risk_max']:
            return ThreatLevel.HIGH_RISK
        else:
            return ThreatLevel.CRITICAL
    
    def _calculate_confidence(
        self,
        forensics: Optional[Dict],
        multimodal: Optional[Dict],
        timeline: Optional[Dict]
    ) -> float:
        """Calculate assessment confidence based on data availability."""
        confidence = 60  # Base confidence from model
        
        if forensics:
            confidence += 15
            if forensics.get('frame_count', 0) > 50:
                confidence += 5
        
        if multimodal:
            confidence += 10
            if multimodal.get('audio_features', {}).get('is_valid'):
                confidence += 5
        
        if timeline:
            confidence += 5
        
        return min(95, confidence)
    
    def _generate_explanation(
        self,
        level: ThreatLevel,
        score: float,
        components: Dict[str, float],
        risks: List[str]
    ) -> str:
        """Generate human-readable explanation."""
        
        level_descriptions = {
            ThreatLevel.SAFE: 
                "Analysis indicates this content is likely authentic. "
                "Multiple verification methods show consistent results "
                "within expected parameters for genuine content.",
            
            ThreatLevel.SUSPICIOUS:
                "Analysis shows some indicators that warrant further investigation. "
                "While not definitively manipulated, certain signals deviate from "
                "expected patterns for authentic content.",
            
            ThreatLevel.HIGH_RISK:
                "Strong indicators of potential manipulation detected. "
                "Multiple analysis methods have identified concerning patterns "
                "consistent with known deepfake techniques.",
            
            ThreatLevel.CRITICAL:
                "CRITICAL: Very strong evidence of manipulation detected. "
                "Analysis shows clear signs of synthetic or manipulated content. "
                "This content should be treated as potentially dangerous.",
            
            ThreatLevel.UNKNOWN:
                "Unable to determine authenticity with sufficient confidence. "
                "Additional analysis or manual review is recommended."
        }
        
        base = level_descriptions[level]
        score_str = f"\n\nOverall threat score: {score:.1f}/100. "
        
        # Add top contributing components
        top_component = max(components, key=components.get)
        score_str += f"Primary concern: {top_component.replace('_', ' ')} ({components[top_component]:.1f}/100)."
        
        if risks:
            risk_str = f"\n\nKey risk factors: {'; '.join(risks[:3])}"
        else:
            risk_str = ""
        
        return base + score_str + risk_str
    
    def _generate_recommendations(
        self,
        level: ThreatLevel,
        risks: List[str]
    ) -> List[str]:
        """Generate action recommendations."""
        
        recommendations = {
            ThreatLevel.SAFE: [
                "Content appears authentic, but verify source if high-stakes",
                "Check metadata and chain of custody for additional assurance",
                "Consider context and source credibility"
            ],
            ThreatLevel.SUSPICIOUS: [
                "Recommend manual review by trained analyst",
                "Cross-reference with known authentic content from the same source",
                "Check for additional corroborating evidence",
                "Consider running additional verification tools"
            ],
            ThreatLevel.HIGH_RISK: [
                "Do NOT use this content without thorough verification",
                "Escalate to security team for professional analysis",
                "Attempt to locate original source content",
                "Document chain of custody for the content",
                "Consider potential impact if content is used"
            ],
            ThreatLevel.CRITICAL: [
                "BLOCK: Do not publish or distribute this content",
                "Immediately escalate to security/legal team",
                "Preserve all metadata and source information",
                "Document detection for potential legal purposes",
                "Investigate the source and distribution chain"
            ],
            ThreatLevel.UNKNOWN: [
                "Seek additional analysis from specialized tools",
                "Request manual expert review",
                "Do not use content until verified",
                "Collect additional context about content origin"
            ]
        }
        
        return recommendations.get(level, recommendations[ThreatLevel.UNKNOWN])
    
    def to_dict(self, assessment: ThreatAssessment) -> Dict[str, Any]:
        """Convert assessment to dictionary for JSON serialization."""
        return {
            'level': assessment.level.value,
            'level_display': assessment.level_display,
            'overall_score': assessment.overall_score,
            'confidence': assessment.confidence,
            'component_scores': assessment.component_scores,
            'risk_factors': assessment.risk_factors,
            'mitigating_factors': assessment.mitigating_factors,
            'explanation': assessment.explanation,
            'recommendations': assessment.recommendations,
            'color_code': assessment.color_code
        }

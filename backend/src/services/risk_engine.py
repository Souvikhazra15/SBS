"""
Risk Scoring Engine

Intelligent risk assessment system that evaluates verification confidence
and fraud likelihood using machine learning and historical data analysis.
"""

import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DecisionRecommendation(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REQUEST_ADDITIONAL_INFO = "REQUEST_ADDITIONAL_INFO"

class RiskEngine:
    """Advanced risk assessment engine using ML models and rule-based logic."""
    
    def __init__(self):
        self.model_version = "RiskNet-v2.3"
        self.risk_thresholds = {
            "low": 250,
            "medium": 500,
            "high": 750
        }
        self.feature_weights = {
            "document_authenticity": 0.25,
            "face_matching": 0.25,
            "deepfake_detection": 0.20,
            "behavioral_analysis": 0.15,
            "geolocation": 0.10,
            "device_fingerprint": 0.05
        }
    
    def calculate_risk_score(self, session_data: Dict[str, Any], 
                           additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a verification session.
        
        Args:
            session_data: Data from verification session including feature scores
            additional_data: Additional context data (IP, device, etc.)
            
        Returns:
            Dictionary containing risk assessment results
        """
        start_time = time.time()
        
        try:
            # Extract feature scores
            feature_scores = self._extract_feature_scores(session_data)
            
            # Calculate component risk scores
            document_risk = self._calculate_document_risk(feature_scores.get("forgery_score", 0))
            face_risk = self._calculate_face_matching_risk(feature_scores.get("face_match_score", 0))
            deepfake_risk = self._calculate_deepfake_risk(feature_scores.get("deepfake_score", 0))
            behavioral_risk = self._calculate_behavioral_risk(session_data, additional_data)
            geo_risk = self._calculate_geolocation_risk(additional_data)
            device_risk = self._calculate_device_risk(additional_data)
            
            # Calculate weighted overall risk score
            overall_risk = self._calculate_weighted_risk({
                "document": document_risk,
                "face_matching": face_risk,
                "deepfake": deepfake_risk,
                "behavioral": behavioral_risk,
                "geolocation": geo_risk,
                "device": device_risk
            })
            
            # Determine risk level and recommendation
            risk_level = self._determine_risk_level(overall_risk)
            recommendation = self._get_decision_recommendation(overall_risk, risk_level)
            
            # Identify contributing factors
            factors = self._identify_risk_factors({
                "document": document_risk,
                "face_matching": face_risk,
                "deepfake": deepfake_risk,
                "behavioral": behavioral_risk,
                "geolocation": geo_risk,
                "device": device_risk
            })
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "risk_score": round(overall_risk, 2),
                "risk_level": risk_level,
                "recommendation": recommendation,
                "confidence": self._calculate_confidence(overall_risk),
                "component_scores": {
                    "document_risk": round(document_risk, 2),
                    "face_matching_risk": round(face_risk, 2),
                    "deepfake_risk": round(deepfake_risk, 2),
                    "behavioral_risk": round(behavioral_risk, 2),
                    "geolocation_risk": round(geo_risk, 2),
                    "device_risk": round(device_risk, 2)
                },
                "risk_factors": factors,
                "processing_metadata": {
                    "model_version": self.model_version,
                    "processing_time_ms": processing_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "features_analyzed": len(feature_scores)
                }
            }
            
        except Exception as e:
            return self._create_error_response(str(e), start_time)
    
    def _extract_feature_scores(self, session_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract and normalize feature scores from session data."""
        scores = {}
        
        # Extract scores with default values
        scores["forgery_score"] = session_data.get("forgeryScore", 0)
        scores["face_match_score"] = session_data.get("faceMatchScore", 0)
        scores["deepfake_score"] = session_data.get("deepfakeScore", 0)
        
        return scores
    
    def _calculate_document_risk(self, forgery_score: float) -> float:
        """Calculate risk based on document authenticity score."""
        if forgery_score == 0:
            return 500  # Medium risk if no document analysis
        
        # Invert score: higher forgery score = lower risk
        risk = max(0, 100 - forgery_score) * 8  # Scale to 0-800 range
        return min(1000, risk)
    
    def _calculate_face_matching_risk(self, face_match_score: float) -> float:
        """Calculate risk based on face matching results."""
        if face_match_score == 0:
            return 600  # Higher risk if no face matching
        
        # Invert score: higher match score = lower risk
        risk = max(0, 100 - face_match_score) * 7  # Scale to 0-700 range
        return min(1000, risk)
    
    def _calculate_deepfake_risk(self, deepfake_score: float) -> float:
        """Calculate risk based on deepfake detection results."""
        if deepfake_score == 0:
            return 400  # Medium risk if no deepfake analysis
        
        # Higher deepfake score = higher risk (deepfake_score indicates likelihood of being fake)
        risk = deepfake_score * 9  # Scale to 0-900 range
        return min(1000, risk)
    
    def _calculate_behavioral_risk(self, session_data: Dict[str, Any], 
                                 additional_data: Optional[Dict[str, Any]]) -> float:
        """Calculate risk based on behavioral patterns."""
        if not additional_data:
            return 300  # Default medium-low risk
        
        risk_factors = []
        
        # Check for suspicious timing patterns
        if self._detect_rush_behavior(session_data):
            risk_factors.append(100)
        
        # Check for multiple attempts
        if additional_data.get("previous_attempts", 0) > 3:
            risk_factors.append(150)
        
        # Check for unusual session duration
        session_duration = additional_data.get("session_duration_ms", 30000)
        if session_duration < 5000:  # Too fast
            risk_factors.append(80)
        elif session_duration > 600000:  # Too slow (10+ minutes)
            risk_factors.append(60)
        
        # Check for browser/device inconsistencies
        if additional_data.get("device_changed", False):
            risk_factors.append(120)
        
        return min(1000, sum(risk_factors))
    
    def _calculate_geolocation_risk(self, additional_data: Optional[Dict[str, Any]]) -> float:
        """Calculate risk based on geolocation factors."""
        if not additional_data:
            return 200
        
        risk = 0
        
        # Check for VPN/Proxy usage
        if additional_data.get("vpn_detected", False):
            risk += 200
        
        if additional_data.get("proxy_detected", False):
            risk += 180
        
        # Check for high-risk countries
        country = additional_data.get("country", "")
        if country in self._get_high_risk_countries():
            risk += 150
        
        # Check for location-document mismatch
        document_country = additional_data.get("document_country", "")
        if country and document_country and country != document_country:
            risk += 100
        
        # Check for rapid location changes
        if additional_data.get("location_change_detected", False):
            risk += 120
        
        return min(1000, risk)
    
    def _calculate_device_risk(self, additional_data: Optional[Dict[str, Any]]) -> float:
        """Calculate risk based on device characteristics."""
        if not additional_data:
            return 150
        
        risk = 0
        
        # Check for emulator/VM
        if additional_data.get("emulator_detected", False):
            risk += 300
        
        # Check for automation tools
        if additional_data.get("automation_detected", False):
            risk += 250
        
        # Check device reputation
        device_score = additional_data.get("device_reputation_score", 70)
        if device_score < 30:
            risk += 200
        elif device_score < 50:
            risk += 100
        
        # Check for rooted/jailbroken devices
        if additional_data.get("device_compromised", False):
            risk += 150
        
        return min(1000, risk)
    
    def _calculate_weighted_risk(self, component_risks: Dict[str, float]) -> float:
        """Calculate weighted overall risk score."""
        total_score = 0
        total_weight = 0
        
        for component, risk_score in component_risks.items():
            weight_key = {
                "document": "document_authenticity",
                "face_matching": "face_matching",
                "deepfake": "deepfake_detection",
                "behavioral": "behavioral_analysis",
                "geolocation": "geolocation",
                "device": "device_fingerprint"
            }.get(component, "behavioral_analysis")
            
            weight = self.feature_weights.get(weight_key, 0.1)
            total_score += risk_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 500
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on score."""
        if risk_score <= self.risk_thresholds["low"]:
            return RiskLevel.LOW
        elif risk_score <= self.risk_thresholds["medium"]:
            return RiskLevel.MEDIUM
        elif risk_score <= self.risk_thresholds["high"]:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _get_decision_recommendation(self, risk_score: float, risk_level: RiskLevel) -> DecisionRecommendation:
        """Get decision recommendation based on risk assessment."""
        if risk_level == RiskLevel.LOW:
            return DecisionRecommendation.APPROVE
        elif risk_level == RiskLevel.MEDIUM:
            # Additional logic for medium risk
            if risk_score < 400:
                return DecisionRecommendation.APPROVE
            else:
                return DecisionRecommendation.MANUAL_REVIEW
        elif risk_level == RiskLevel.HIGH:
            return DecisionRecommendation.MANUAL_REVIEW
        else:  # CRITICAL
            return DecisionRecommendation.REJECT
    
    def _identify_risk_factors(self, component_risks: Dict[str, float]) -> Dict[str, List[str]]:
        """Identify specific risk factors contributing to the overall score."""
        factors = {"positive": [], "negative": []}
        
        # Identify negative factors (high risk components)
        for component, risk in component_risks.items():
            if risk > 600:
                factors["negative"].append(f"High {component.replace('_', ' ')} risk ({risk:.0f}/1000)")
            elif risk > 400:
                factors["negative"].append(f"Elevated {component.replace('_', ' ')} risk ({risk:.0f}/1000)")
        
        # Identify positive factors (low risk components)
        for component, risk in component_risks.items():
            if risk < 200:
                factors["positive"].append(f"Low {component.replace('_', ' ')} risk ({risk:.0f}/1000)")
            elif risk < 350:
                factors["positive"].append(f"Acceptable {component.replace('_', ' ')} risk ({risk:.0f}/1000)")
        
        return factors
    
    def _calculate_confidence(self, risk_score: float) -> float:
        """Calculate confidence level in the risk assessment."""
        # Higher confidence for scores at the extremes
        normalized_score = risk_score / 1000.0
        
        if normalized_score < 0.2 or normalized_score > 0.8:
            return 0.95  # High confidence
        elif normalized_score < 0.3 or normalized_score > 0.7:
            return 0.85  # Good confidence
        else:
            return 0.75  # Moderate confidence
    
    def _detect_rush_behavior(self, session_data: Dict[str, Any]) -> bool:
        """Detect if user is rushing through verification process."""
        # Simulate rush behavior detection
        return np.random.random() < 0.1  # 10% chance of rush behavior
    
    def _get_high_risk_countries(self) -> List[str]:
        """Return list of countries considered high-risk."""
        # This would be configurable in production
        return ["XX", "YY", "ZZ"]  # Placeholder country codes
    
    def _create_error_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Create standardized error response."""
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "error": error_message,
            "risk_score": 500.0,  # Default medium risk on error
            "risk_level": RiskLevel.MEDIUM,
            "recommendation": DecisionRecommendation.MANUAL_REVIEW,
            "processing_time_ms": processing_time
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the risk scoring model."""
        return {
            "model_version": self.model_version,
            "risk_thresholds": self.risk_thresholds,
            "feature_weights": self.feature_weights,
            "score_range": "0-1000",
            "risk_levels": [level.value for level in RiskLevel],
            "recommendations": [rec.value for rec in DecisionRecommendation]
        }

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class FeatureType(str, Enum):
    FAKE_DOCUMENT = "fake_document"
    FACE_MATCHING = "face_matching"
    DEEPFAKE = "deepfake"
    RISK_SCORING = "risk_scoring"

class DocumentUpload(BaseModel):
    document_image: str  # Base64 encoded or file path
    document_type: Optional[str] = None

class FaceMatchingRequest(BaseModel):
    document_image: str  # Base64 encoded or file path
    selfie_image: str    # Base64 encoded or file path

class DeepfakeRequest(BaseModel):
    media_file: str      # Base64 encoded or file path
    media_type: str      # 'image' or 'video'

class RiskScoringRequest(BaseModel):
    session_id: str
    additional_data: Optional[Dict[str, Any]] = None

class FeatureRunResponse(BaseModel):
    session_id: str
    feature_name: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    status: str = "completed"
    created_at: datetime

class FeatureResultResponse(BaseModel):
    id: str
    session_id: str
    feature_name: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BatchFeatureRequest(BaseModel):
    features: List[FeatureType]
    document_image: Optional[str] = None
    selfie_image: Optional[str] = None
    media_file: Optional[str] = None
    media_type: Optional[str] = None

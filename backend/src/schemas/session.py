from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class VerificationDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    PENDING = "PENDING"

class VerificationSessionCreate(BaseModel):
    document_path: Optional[str] = None
    selfie_path: Optional[str] = None

class VerificationSessionUpdate(BaseModel):
    forgery_score: Optional[float] = None
    face_match_score: Optional[float] = None
    deepfake_score: Optional[float] = None
    risk_score: Optional[float] = None
    decision: Optional[VerificationDecision] = None

class VerificationSessionResponse(BaseModel):
    id: str
    userId: str
    documentPath: Optional[str]
    selfiePath: Optional[str]
    forgeryScore: Optional[float]
    faceMatchScore: Optional[float]
    deepfakeScore: Optional[float]
    riskScore: Optional[float]
    decision: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class SessionSummaryResponse(BaseModel):
    session: VerificationSessionResponse
    feature_results: List[Dict[str, Any]]
    overall_status: str
    risk_level: str
    recommendations: List[str]

class SessionListResponse(BaseModel):
    sessions: List[VerificationSessionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool

class SessionStatsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    pending_sessions: int
    approved_sessions: int
    rejected_sessions: int
    manual_review_sessions: int
    average_processing_time: Optional[float] = None
    success_rate: Optional[float] = None

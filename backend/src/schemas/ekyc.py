"""
E-KYC Schemas

Pydantic models for e-KYC verification requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EkycStatusEnum(str, Enum):
    """E-KYC session status"""
    PENDING = "PENDING"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    SELFIE_UPLOADED = "SELFIE_UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class EkycDecisionEnum(str, Enum):
    """E-KYC verification decision"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PENDING = "PENDING"


class DocumentTypeEnum(str, Enum):
    """Document type"""
    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    NATIONAL_ID = "NATIONAL_ID"
    RESIDENCE_PERMIT = "RESIDENCE_PERMIT"
    VOTER_ID = "VOTER_ID"


# ===== Request Models =====

class EkycSessionStartRequest(BaseModel):
    """Request to start a new e-KYC session"""
    pass  # No required fields, user comes from JWT


class DocumentUploadRequest(BaseModel):
    """Document upload metadata"""
    session_id: str = Field(..., description="E-KYC session ID")
    document_type: DocumentTypeEnum = Field(..., description="Type of document")


class SelfieUploadRequest(BaseModel):
    """Selfie upload metadata"""
    session_id: str = Field(..., description="E-KYC session ID")


class EkycRunRequest(BaseModel):
    """Request to run e-KYC verification"""
    session_id: str = Field(..., description="E-KYC session ID to process")


# ===== Response Models =====

class EkycDocumentResponse(BaseModel):
    """E-KYC document response"""
    id: str
    session_id: str
    type: str
    front_image_url: str
    back_image_url: Optional[str]
    document_number: Optional[str]
    full_name: Optional[str]
    date_of_birth: Optional[str]
    expiry_date: Optional[str]
    issuing_country: Optional[str]
    is_authentic: Optional[bool]
    confidence_score: Optional[float]
    tampering_detected: bool
    uploaded_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class EkycResultResponse(BaseModel):
    """E-KYC verification result response"""
    id: str
    session_id: str
    verification_type: str
    score: float
    is_passed: bool
    confidence: Optional[float]
    details: Optional[Dict[str, Any]]
    model_version: Optional[str]
    processed_at: datetime
    processing_time: Optional[int]

    class Config:
        from_attributes = True


class EkycSessionResponse(BaseModel):
    """E-KYC session response"""
    id: str
    user_id: str
    session_id: str
    status: str
    decision: str
    document_score: Optional[float]
    face_match_score: Optional[float]
    liveness_score: Optional[float]
    overall_score: Optional[float]
    rejection_reason: Optional[str]
    review_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    documents: List[EkycDocumentResponse] = []
    results: List[EkycResultResponse] = []

    class Config:
        from_attributes = True


class EkycSessionHistoryResponse(BaseModel):
    """E-KYC session history response"""
    sessions: List[EkycSessionResponse]
    total: int
    page: int
    page_size: int

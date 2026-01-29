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
    session_id: str = Field(..., alias="sessionId")
    type: str
    front_image_url: str = Field(..., alias="frontImageUrl")
    back_image_url: Optional[str] = Field(None, alias="backImageUrl")
    document_number: Optional[str] = Field(None, alias="documentNumber")
    full_name: Optional[str] = Field(None, alias="fullName")
    date_of_birth: Optional[str] = Field(None, alias="dateOfBirth")
    expiry_date: Optional[str] = Field(None, alias="expiryDate")
    issuing_country: Optional[str] = Field(None, alias="issuingCountry")
    is_authentic: Optional[bool] = Field(None, alias="isAuthentic")
    confidence_score: Optional[float] = Field(None, alias="confidenceScore")
    tampering_detected: bool = Field(..., alias="tamperingDetected")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    processed_at: Optional[datetime] = Field(None, alias="processedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class EkycResultResponse(BaseModel):
    """E-KYC verification result response"""
    id: str
    session_id: str = Field(..., alias="sessionId")
    verification_type: str = Field(..., alias="verificationType")
    score: float
    is_passed: bool = Field(..., alias="isPassed")
    confidence: Optional[float]
    details: Optional[Dict[str, Any]]
    model_version: Optional[str] = Field(None, alias="modelVersion")
    processed_at: datetime = Field(..., alias="processedAt")
    processing_time: Optional[int] = Field(None, alias="processingTime")

    class Config:
        from_attributes = True
        populate_by_name = True


class EkycSessionResponse(BaseModel):
    """E-KYC session response"""
    id: str
    user_id: Optional[str] = Field(None, alias="userId")
    session_id: str = Field(..., alias="sessionId")
    status: str
    decision: str
    document_score: Optional[float] = Field(None, alias="documentScore")
    face_match_score: Optional[float] = Field(None, alias="faceMatchScore")
    liveness_score: Optional[float] = Field(None, alias="livenessScore")
    overall_score: Optional[float] = Field(None, alias="overallScore")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")
    review_notes: Optional[str] = Field(None, alias="reviewNotes")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    documents: List[EkycDocumentResponse] = []
    results: List[EkycResultResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class EkycSessionHistoryResponse(BaseModel):
    """E-KYC session history response"""
    sessions: List[EkycSessionResponse]
    total: int
    page: int
    page_size: int

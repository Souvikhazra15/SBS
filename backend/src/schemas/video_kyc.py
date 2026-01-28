"""
Video KYC Schemas - Request/Response validation for Video KYC API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VideoKYCStatusEnum(str, Enum):
    IDLE = "IDLE"
    IN_PROGRESS = "IN_PROGRESS"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    AI_ANALYSIS = "AI_ANALYSIS"
    AGENT_REVIEW = "AGENT_REVIEW"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class VerificationDecisionEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class MessageTypeEnum(str, Enum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


# ============================================
# Session Management
# ============================================

class VideoKYCSessionCreate(BaseModel):
    """Create a new Video KYC session"""
    pass


class VideoKYCSessionUpdate(BaseModel):
    """Update Video KYC session data"""
    name: Optional[str] = None
    dateOfBirth: Optional[str] = None
    address: Optional[str] = None
    income: Optional[str] = None
    employment: Optional[str] = None
    aadhar: Optional[str] = None
    pan: Optional[str] = None
    currentStep: Optional[int] = None


class VideoKYCSessionResponse(BaseModel):
    """Video KYC session response"""
    id: str
    userId: str
    sessionStatus: VideoKYCStatusEnum
    currentStep: int
    totalSteps: int
    name: Optional[str] = None
    dateOfBirth: Optional[str] = None
    address: Optional[str] = None
    income: Optional[str] = None
    employment: Optional[str] = None
    aadhar: Optional[str] = None
    pan: Optional[str] = None
    profileImagePath: Optional[str] = None
    signatureImagePath: Optional[str] = None
    documentImagePath: Optional[str] = None
    documentVerified: bool = False
    faceMatched: bool = False
    livenessChecked: bool = False
    riskScore: Optional[float] = None
    forgeryScore: Optional[float] = None
    faceMatchScore: Optional[float] = None
    deepfakeScore: Optional[float] = None
    finalDecision: VerificationDecisionEnum
    sessionStartedAt: datetime
    sessionCompletedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Question & Answer Management
# ============================================

class VideoKYCQuestionCreate(BaseModel):
    """Create a question in Video KYC session"""
    sessionId: str
    questionText: str
    questionType: str
    questionOrder: int
    validationRules: Optional[Dict[str, Any]] = None
    required: bool = True


class VideoKYCQuestionResponse(BaseModel):
    """Video KYC question response"""
    id: str
    sessionId: str
    questionText: str
    questionType: str
    questionOrder: int
    validationRules: Optional[Dict[str, Any]] = None
    required: bool
    askedAt: datetime

    class Config:
        from_attributes = True


class VideoKYCAnswerCreate(BaseModel):
    """Submit an answer to a Video KYC question"""
    sessionId: str
    questionId: str
    answerText: Optional[str] = None
    answerType: str = "text"  # text, image, audio
    responseTime: Optional[int] = None


class VideoKYCAnswerResponse(BaseModel):
    """Video KYC answer response"""
    id: str
    sessionId: str
    questionId: str
    answerText: Optional[str] = None
    answerType: str
    imageUrl: Optional[str] = None
    audioUrl: Optional[str] = None
    isValid: bool
    validationErrors: Optional[Dict[str, Any]] = None
    answeredAt: datetime
    responseTime: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================
# Chat Messages
# ============================================

class VideoKYCChatMessageCreate(BaseModel):
    """Create a chat message in Video KYC session"""
    sessionId: str
    messageText: str
    messageType: MessageTypeEnum


class VideoKYCChatMessageResponse(BaseModel):
    """Video KYC chat message response"""
    id: str
    sessionId: str
    messageText: str
    messageType: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============================================
# File Upload
# ============================================

class VideoKYCFileUploadRequest(BaseModel):
    """Video KYC file upload request"""
    sessionId: str
    fileType: str  # profile, signature, document
    name: str
    dob: Optional[str] = None


class VideoKYCFileUploadResponse(BaseModel):
    """Video KYC file upload response"""
    success: bool
    sessionId: str
    filePath: str
    fileType: str
    message: str


# ============================================
# Verification Results
# ============================================

class VideoKYCVerificationResultCreate(BaseModel):
    """Create a verification result"""
    sessionId: str
    verificationType: str  # document, face_match, liveness, deepfake, risk
    score: float
    confidence: Optional[float] = None
    isPassed: bool
    details: Optional[Dict[str, Any]] = None
    modelVersion: Optional[str] = None
    processingTime: Optional[int] = None


class VideoKYCVerificationResultResponse(BaseModel):
    """Video KYC verification result response"""
    id: str
    sessionId: str
    verificationType: str
    score: float
    confidence: Optional[float] = None
    isPassed: bool
    details: Optional[Dict[str, Any]] = None
    modelVersion: Optional[str] = None
    processedAt: datetime
    processingTime: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================
# AI Analysis
# ============================================

class VideoKYCAIAnalysisRequest(BaseModel):
    """Request AI analysis for Video KYC session"""
    sessionId: str


class VideoKYCAIAnalysisResponse(BaseModel):
    """Video KYC AI analysis response"""
    success: bool
    sessionId: str
    documentVerified: bool
    faceMatched: bool
    livenessChecked: bool
    forgeryScore: Optional[float] = None
    faceMatchScore: Optional[float] = None
    deepfakeScore: Optional[float] = None
    riskScore: Optional[float] = None
    recommendation: str
    details: Dict[str, Any]


# ============================================
# Session Completion
# ============================================

class VideoKYCSessionCompleteRequest(BaseModel):
    """Complete Video KYC session"""
    sessionId: str
    agentName: Optional[str] = None
    agentReviewNotes: Optional[str] = None
    finalDecision: VerificationDecisionEnum
    rejectionReason: Optional[str] = None


class VideoKYCSessionCompleteResponse(BaseModel):
    """Video KYC session completion response"""
    success: bool
    sessionId: str
    finalDecision: VerificationDecisionEnum
    message: str
    session: VideoKYCSessionResponse


# ============================================
# Session History
# ============================================

class VideoKYCSessionHistoryResponse(BaseModel):
    """Video KYC session history"""
    sessions: List[VideoKYCSessionResponse]
    total: int
    page: int
    pageSize: int


# ============================================
# ID Document OCR
# ============================================

class VideoKYCIdCaptureResponse(BaseModel):
    """Response from ID capture and OCR"""
    success: bool
    idNumber: Optional[str] = None
    idType: Optional[str] = None
    confidence: Optional[float] = None
    fullText: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[int] = None
    quality_score: Optional[float] = None
    message: Optional[str] = None

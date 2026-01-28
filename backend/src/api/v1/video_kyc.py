"""
Video KYC API Routes - Video KYC verification endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from typing import Optional
import logging
from src.config.prisma import get_db_pool
from src.utils.auth import get_current_user
from src.schemas.video_kyc import (
    VideoKYCSessionCreate,
    VideoKYCSessionResponse,
    VideoKYCSessionUpdate,
    VideoKYCQuestionCreate,
    VideoKYCQuestionResponse,
    VideoKYCAnswerCreate,
    VideoKYCAnswerResponse,
    VideoKYCChatMessageCreate,
    VideoKYCChatMessageResponse,
    VideoKYCFileUploadResponse,
    VideoKYCVerificationResultCreate,
    VideoKYCVerificationResultResponse,
    VideoKYCAIAnalysisRequest,
    VideoKYCAIAnalysisResponse,
    VideoKYCSessionCompleteRequest,
    VideoKYCSessionCompleteResponse,
    VideoKYCSessionHistoryResponse,
    VideoKYCIdCaptureResponse,
)
from src.services.video_kyc_service import VideoKYCService
from src.services.ocr_service import OCRService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video-kyc", tags=["Video KYC"])


# ============================================
# Session Management
# ============================================

@router.post("/session/create", response_model=VideoKYCSessionResponse)
async def create_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        session = await service.create_session(
            user_id=current_user["id"],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=VideoKYCSessionResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get Video KYC session by ID"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        session = await service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify user owns this session
        if session["userId"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/session/{session_id}/update", response_model=VideoKYCSessionResponse)
async def update_session(
    session_id: str,
    update_data: VideoKYCSessionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(session_id)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        updated_session = await service.update_session(session_id, update_data)
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Question & Answer Management
# ============================================

@router.post("/question/create", response_model=VideoKYCQuestionResponse)
async def create_question(
    question_data: VideoKYCQuestionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a question in Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(question_data.sessionId)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        question = await service.add_question(question_data)
        return question
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer/submit", response_model=VideoKYCAnswerResponse)
async def submit_answer(
    answer_data: VideoKYCAnswerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Submit an answer to a Video KYC question"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(answer_data.sessionId)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        answer = await service.add_answer(answer_data)
        return answer
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Chat Messages
# ============================================

@router.post("/chat/message", response_model=VideoKYCChatMessageResponse)
async def add_chat_message(
    message_data: VideoKYCChatMessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a chat message to Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(message_data.sessionId)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        message = await service.add_chat_message(message_data)
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ID Document OCR Capture
# ============================================

@router.post("/capture-id", response_model=VideoKYCIdCaptureResponse)
async def capture_id_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Capture and process ID document image with OCR
    
    Extracts ID number from document using OCR and saves to database.
    """
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    ocr_service = OCRService()
    
    try:
        logger.info(f"[VIDEO-KYC] ID capture request for session: {session_id}")
        
        # Verify session exists and user owns it
        session = await service.get_session(session_id)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate file is image
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        logger.info(f"[VIDEO-KYC] ID frame captured, size: {file.size} bytes")
        
        # Read image data
        image_data = await file.read()
        
        # Process with OCR
        logger.info("[OCR] Running OCR on ID document")
        ocr_result = await ocr_service.process_id_document(image_data)
        
        if not ocr_result['success']:
            logger.warning(f"[OCR] Failed: {ocr_result.get('error', 'Unknown error')}")
            return VideoKYCIdCaptureResponse(
                success=False,
                error=ocr_result.get('error', 'OCR processing failed'),
                processing_time=ocr_result.get('processing_time'),
                quality_score=ocr_result.get('quality_score'),
                message="Please ensure ID is clear, well-lit, and inside the frame"
            )
        
        # Extract data
        id_number = ocr_result['idNumber']
        id_type = ocr_result.get('idType', 'unknown')
        confidence = ocr_result['confidence']
        full_text = ocr_result.get('fullText', '')
        
        logger.info(f"[OCR] Extracted ID: {id_number} (type: {id_type}, confidence: {confidence:.3f})")
        
        # Save to database
        logger.info("[DB] Saving document to database")
        document_id = await service.save_id_document(
            session_id=session_id,
            id_number=id_number,
            full_text=full_text,
            ocr_json=ocr_result,
            confidence=confidence
        )
        
        logger.info(f"[DB] Document saved: {document_id}")
        
        return VideoKYCIdCaptureResponse(
            success=True,
            idNumber=id_number,
            idType=id_type,
            confidence=round(confidence, 3),
            fullText=full_text,
            processing_time=ocr_result.get('processing_time'),
            quality_score=ocr_result.get('quality_score'),
            message=f"ID extracted successfully: {id_number}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VIDEO-KYC] ID capture failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# File Upload
# ============================================

@router.post("/upload", response_model=VideoKYCFileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    file_type: str = Form(...),
    name: str = Form(...),
    dob: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload image file for Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(session_id)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate file type
        if file_type not in ["profile", "signature", "document"]:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Read file data
        file_data = await file.read()
        
        # Save file
        file_path = await service.save_uploaded_file(
            session_id=session_id,
            file_data=file_data,
            file_type=file_type,
            filename=file.filename or "image.png"
        )
        
        return {
            "success": True,
            "sessionId": session_id,
            "filePath": file_path,
            "fileType": file_type,
            "message": f"{file_type.capitalize()} image uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Verification Results
# ============================================

@router.post("/verification/result", response_model=VideoKYCVerificationResultResponse)
async def add_verification_result(
    result_data: VideoKYCVerificationResultCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a verification result to Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(result_data.sessionId)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        result = await service.add_verification_result(result_data)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AI Analysis
# ============================================

@router.post("/analysis/run", response_model=VideoKYCAIAnalysisResponse)
async def run_ai_analysis(
    request_data: VideoKYCAIAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Run AI analysis on Video KYC session"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(request_data.sessionId)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        analysis_results = await service.run_ai_analysis(request_data.sessionId)
        
        return {
            "success": True,
            "sessionId": request_data.sessionId,
            "documentVerified": analysis_results["documentVerified"],
            "faceMatched": analysis_results["faceMatched"],
            "livenessChecked": analysis_results["livenessChecked"],
            "forgeryScore": analysis_results["forgeryScore"],
            "faceMatchScore": analysis_results["faceMatchScore"],
            "deepfakeScore": analysis_results["deepfakeScore"],
            "riskScore": analysis_results["riskScore"],
            "recommendation": analysis_results["recommendation"],
            "details": analysis_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Session Completion
# ============================================

@router.post("/session/complete", response_model=VideoKYCSessionCompleteResponse)
async def complete_session(
    request_data: VideoKYCSessionCompleteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Complete Video KYC session with final decision"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(request_data.sessionId)
        if not session or session["userId"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        completed_session = await service.complete_session(
            session_id=request_data.sessionId,
            final_decision=request_data.finalDecision,
            agent_name=request_data.agentName,
            agent_review_notes=request_data.agentReviewNotes,
            rejection_reason=request_data.rejectionReason
        )
        
        return {
            "success": True,
            "sessionId": request_data.sessionId,
            "finalDecision": request_data.finalDecision,
            "message": "Session completed successfully",
            "session": completed_session
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Session History
# ============================================

@router.get("/session/history", response_model=VideoKYCSessionHistoryResponse)
async def get_session_history(
    limit: int = 10,
    page: int = 1,
    current_user: dict = Depends(get_current_user)
):
    """Get user's Video KYC session history"""
    
    pool = get_db_pool()
    service = VideoKYCService(pool)
    
    try:
        skip = (page - 1) * limit
        sessions = await service.get_user_sessions(
            user_id=current_user["id"],
            limit=limit,
            skip=skip
        )
        
        total = await service.get_session_count(current_user["id"])
        
        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "pageSize": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

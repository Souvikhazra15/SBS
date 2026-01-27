"""
Video KYC API Routes - Video KYC verification endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from typing import Optional
from ..config.prisma import get_db_pool
from ..utils.auth import get_current_user
from ..schemas.video_kyc import (
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
)
from ..services.video_kyc_service import VideoKYCService

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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Get Video KYC session by ID"""
    
    service = VideoKYCService(db)
    
    try:
        session = await service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify user owns this session
        if session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Update Video KYC session"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(session_id)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Create a question in Video KYC session"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(question_data.sessionId)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Submit an answer to a Video KYC question"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(answer_data.sessionId)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Add a chat message to Video KYC session"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(message_data.sessionId)
        if not session or session.userId != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        message = await service.add_chat_message(message_data)
        return message
        
    except HTTPException:
        raise
    except Exception as e:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Upload image file for Video KYC session"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(session_id)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Add a verification result to Video KYC session"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(result_data.sessionId)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Run AI analysis on Video KYC session"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(request_data.sessionId)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Complete Video KYC session with final decision"""
    
    service = VideoKYCService(db)
    
    try:
        # Verify session exists and user owns it
        session = await service.get_session(request_data.sessionId)
        if not session or session.userId != current_user["id"]:
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
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """Get user's Video KYC session history"""
    
    service = VideoKYCService(db)
    
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

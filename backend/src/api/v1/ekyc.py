"""
E-KYC API Routes

RESTful endpoints for e-KYC verification including document upload,
selfie capture, verification processing, and session history.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import Optional
import logging

from src.schemas.ekyc import (
    EkycSessionStartRequest,
    EkycSessionResponse,
    EkycRunRequest,
    EkycSessionHistoryResponse,
)
from src.services.ekyc_service import EkycService
from src.utils.auth import get_current_user
from src.config.prisma import prisma

router = APIRouter(prefix="/e-kyc", tags=["E-KYC"])
logger = logging.getLogger(__name__)


@router.post("/start", response_model=EkycSessionResponse)
async def start_ekyc_session(
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new e-KYC verification session
    
    - **Requires**: JWT authentication
    - **Returns**: New e-KYC session with unique session ID
    
    The session will be tied to the authenticated user.
    """
    try:
        service = EkycService(prisma)
        
        session = await service.create_session(
            user_id=current_user["id"],
            ip_address=None,  # Can be extracted from request
            user_agent=None,  # Can be extracted from request
        )
        
        logger.info(f"[EKYC] Session created: {session.sessionId} for user: {current_user['id']}")
        
        return session
        
    except Exception as e:
        logger.error(f"[EKYC] Failed to start session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start e-KYC session: {str(e)}"
        )


@router.post("/upload-document")
async def upload_document(
    session_id: str = Form(...),
    document_type: str = Form(...),
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload identity document to e-KYC session
    
    - **Requires**: JWT authentication
    - **session_id**: E-KYC session ID
    - **document_type**: Type of document (PASSPORT, DRIVERS_LICENSE, etc.)
    - **front_image**: Front image of document
    - **back_image**: Back image of document (optional)
    
    Returns uploaded document details.
    """
    try:
        service = EkycService(prisma)
        
        # Verify session belongs to user
        session = await service.get_session(session_id)
        if not session or session.userId != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # In production, upload files to cloud storage (S3, etc.)
        # For now, we'll use placeholder URLs
        front_url = f"/uploads/documents/{session_id}_front.jpg"
        back_url = f"/uploads/documents/{session_id}_back.jpg" if back_image else None
        
        logger.info(f"[EKYC] Document uploaded for session: {session_id}")
        
        document = await service.upload_document(
            session_id=session.id,
            document_type=document_type,
            front_image_url=front_url,
            back_image_url=back_url,
        )
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "session_id": session_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Failed to upload document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/upload-selfie")
async def upload_selfie(
    session_id: str = Form(...),
    selfie_image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload selfie image to e-KYC session
    
    - **Requires**: JWT authentication
    - **session_id**: E-KYC session ID
    - **selfie_image**: Selfie/video capture image
    
    Returns upload confirmation.
    """
    try:
        service = EkycService(prisma)
        
        # Verify session belongs to user
        session = await service.get_session(session_id)
        if not session or session.userId != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # In production, upload to cloud storage
        selfie_url = f"/uploads/selfies/{session_id}_selfie.jpg"
        
        logger.info(f"[EKYC] Selfie uploaded for session: {session_id}")
        
        await service.upload_selfie(
            session_id=session.id,
            selfie_url=selfie_url,
        )
        
        return {
            "success": True,
            "message": "Selfie uploaded successfully",
            "session_id": session_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Failed to upload selfie: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload selfie: {str(e)}"
        )


@router.post("/run", response_model=EkycSessionResponse)
async def run_ekyc_verification(
    request: EkycRunRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Run complete e-KYC verification process
    
    - **Requires**: JWT authentication
    - **session_id**: E-KYC session ID to process
    
    Returns verification results including:
    - Document authenticity score
    - Face matching score
    - Liveness detection score
    - Overall score
    - Final decision (APPROVED/REJECTED/REVIEW_REQUIRED)
    """
    try:
        service = EkycService(prisma)
        
        # Verify session belongs to user
        session = await service.get_session(request.session_id)
        if not session or session.userId != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        logger.info(f"[EKYC] Running verification for session: {request.session_id}")
        
        result = await service.run_verification(session.id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/{session_id}", response_model=EkycSessionResponse)
async def get_ekyc_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get e-KYC session details by ID
    
    - **Requires**: JWT authentication
    - **session_id**: E-KYC session ID
    
    Returns session with all documents and verification results.
    """
    try:
        service = EkycService(prisma)
        
        session = await service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify user owns this session
        if session.userId != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Failed to fetch session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session: {str(e)}"
        )


@router.get("/history/my", response_model=EkycSessionHistoryResponse)
async def get_my_ekyc_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get e-KYC session history for current user
    
    - **Requires**: JWT authentication
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Returns paginated list of user's e-KYC sessions.
    """
    try:
        service = EkycService(prisma)
        
        skip = (page - 1) * page_size
        
        sessions = await service.get_user_sessions(
            user_id=current_user["id"],
            skip=skip,
            take=page_size,
        )
        
        total = await service.count_user_sessions(current_user["id"])
        
        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        
    except Exception as e:
        logger.error(f"[EKYC] Failed to fetch history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )

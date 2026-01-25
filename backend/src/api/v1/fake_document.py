"""
Fake Document Detection API Routes

RESTful endpoints for document authenticity verification.
Provides document analysis and fraud detection capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import traceback
import base64
import uuid

from src.schemas.feature import DocumentUpload, FeatureRunResponse
from src.schemas.session import VerificationSessionResponse
from src.services.fake_document_service import FakeDocumentService
from src.utils.auth import get_current_active_user
from src.config.prisma import prisma

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/fake-document", tags=["Fake Document Detection"])
service = FakeDocumentService()

@router.post("/run", response_model=FeatureRunResponse)
async def run_fake_document_detection(
    document_upload: DocumentUpload,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Run fake document detection on uploaded document.
    
    - **document_image**: Base64 encoded document image
    - **document_type**: Optional document type hint (passport, drivers_license, etc.)
    
    Returns detailed analysis of document authenticity including:
    - Forgery score (0-100)
    - Security feature analysis
    - Tampering detection results
    - OCR validation
    """
    try:
        # Run document analysis
        analysis_result = service.analyze_document(
            document_upload.document_image,
            document_upload.document_type
        )
        
        if "error" in analysis_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document analysis failed: {analysis_result['error']}"
            )
        
        # Create or update verification session
        session = await prisma.verificationsession.create({
            "userId": current_user["id"],
            "documentPath": "base64_document",  # In production, store file reference
            "forgeryScore": analysis_result["forgery_score"]
        })
        
        # Store feature result
        await prisma.featureresult.create({
            "sessionId": session.id,
            "featureName": "fake_document",
            "score": analysis_result["forgery_score"],
            "metadata": analysis_result
        })
        
        return FeatureRunResponse(
            session_id=session.id,
            feature_name="fake_document",
            score=analysis_result["forgery_score"],
            metadata=analysis_result,
            processing_time_ms=analysis_result.get("processing_time_ms"),
            status="completed",
            created_at=session.createdAt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{session_id}", response_model=FeatureRunResponse)
async def get_fake_document_result(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Retrieve fake document detection results for a specific session.
    
    - **session_id**: UUID of the verification session
    
    Returns the stored analysis results including scores and metadata.
    """
    try:
        # Find the feature result
        feature_result = await prisma.featureresult.find_first(
            where={
                "sessionId": session_id,
                "featureName": "fake_document",
                "session": {
                    "userId": current_user["id"]  # Ensure user owns this session
                }
            },
            include={
                "session": True
            }
        )
        
        if not feature_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fake document result not found for this session"
            )
        
        return FeatureRunResponse(
            session_id=feature_result.sessionId,
            feature_name=feature_result.featureName,
            score=feature_result.score,
            metadata=feature_result.metadata,
            status="completed",
            created_at=feature_result.createdAt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    document_type: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_active_user)  # Make optional
):
    """
    Upload document file for analysis with live progress logging.
    
    - **file**: Document image file (JPEG, PNG, etc.)
    - **document_type**: Optional document type hint
    
    Returns structured JSON response with analysis results.
    """
    session_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[UPLOAD] File received: {file.filename} ({file.content_type})")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            logger.warning(f"[UPLOAD] Invalid file type: {file.content_type}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Only image files are supported (JPEG, PNG, BMP, TIFF)"
                }
            )
        
        # Validate file size (max 10MB)
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"[UPLOAD] File size: {file_size_mb:.2f} MB")
        
        if len(content) > 10 * 1024 * 1024:  # 10MB
            logger.warning(f"[UPLOAD] File too large: {file_size_mb:.2f} MB")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed (10 MB)"
                }
            )
        
        logger.info(f"[PREPROCESS] Converting image to base64...")
        # Convert to base64 for processing
        base64_content = base64.b64encode(content).decode('utf-8')
        
        logger.info(f"[OCR] Starting text extraction...")
        logger.info(f"[FORGERY] Analyzing document for tampering...")
        
        # Run analysis
        analysis_result = service.analyze_document(base64_content, document_type)
        
        if "error" in analysis_result:
            logger.error(f"[FORGERY] Analysis failed: {analysis_result['error']}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Document analysis failed: {analysis_result['error']}"
                }
            )
        
        logger.info(f"[FORGERY] Analysis complete - Score: {analysis_result.get('forgery_score', 0)}")
        
        # Only save to DB if user is authenticated
        if current_user:
            logger.info(f"[DB] Saving results to database...")
            try:
                session = await prisma.verificationSession.create({
                    "userId": current_user["id"],
                    "documentPath": file.filename,
                    "forgeryScore": analysis_result.get("forgery_score", 0.0),
                    "decision": "APPROVED" if analysis_result.get("is_authentic", False) else "REJECTED"
                })
                session_id = session["id"]
                
                await prisma.featureResult.create({
                    "sessionId": session_id,
                    "featureName": "fake_document",
                    "score": analysis_result.get("forgery_score", 0.0),
                    "metadata": analysis_result
                })
                
                logger.info(f"[DB] Results saved successfully - Session ID: {session_id}")
            except Exception as db_error:
                logger.error(f"[DB] Database error: {str(db_error)}")
        else:
            logger.info(f"[DEMO] Running in demo mode (no user authentication)")
        
        logger.info(f"[DONE] Response sent - Processing time: {analysis_result.get('processing_time_ms', 0)} ms")
        
        # Return structured response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "sessionId": session_id,
                "forgeryScore": analysis_result.get("forgery_score", 0.0),
                "confidence": analysis_result.get("confidence_level", 0.0),
                "documentType": document_type or "unknown",
                "isAuthentic": analysis_result.get("is_authentic", False),
                "issues": [
                    "Tampering detected" if analysis_result.get("tampering_detected") else None,
                    "Hologram invalid" if not analysis_result.get("hologram_valid") else None,
                    "OCR inconsistent" if not analysis_result.get("ocr_consistent") else None
                ],
                "metadata": {
                    "tamperingDetected": analysis_result.get("tampering_detected", False),
                    "ocrExtracted": analysis_result.get("ocr_validation", {}),
                    "securityFeatures": analysis_result.get("security_features", {}).get("features_detected", {})
                }
            }
        )
        
    except HTTPException as he:
        logger.error(f"[ERROR] HTTP Exception: {str(he)}")
        return JSONResponse(
            status_code=he.status_code,
            content={
                "success": False,
                "error": he.detail
            }
        )
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }
        )
    
@router.get("/info")
async def get_service_info():
    """
    Get information about the fake document detection service.
    
    Returns model version, supported document types, and capabilities.
    """
    return {
        "service_name": "Fake Document Detection",
        "version": service.model_version,
        "supported_document_types": service.get_supported_document_types(),
        "capabilities": [
            "Security feature detection",
            "Tampering analysis",
            "Hologram verification",
            "OCR validation",
            "Multi-country support"
        ],
        "max_file_size": "10MB",
        "supported_formats": ["JPEG", "PNG", "BMP", "TIFF"]
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    """
    try:
        # Test service availability
        model_info = {
            "status": "healthy",
            "service": "fake_document_detection",
            "timestamp": datetime.utcnow().isoformat(),
            "version": service.model_version
        }
        logger.info("[HEALTH] Health check passed")
        return JSONResponse(status_code=200, content=model_info)
    except Exception as e:
        logger.error(f"[HEALTH] Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

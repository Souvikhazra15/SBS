"""
Deepfake Detection API Routes

RESTful endpoints for synthetic media and deepfake detection.
Supports both image and video analysis with real trained model.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import tempfile
import os
import uuid
import traceback

from src.services.deepfake_service import DeepfakeService
from src.utils.auth import get_current_active_user
from src.config.prisma import prisma

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deepfake", tags=["Deepfake Detection"])
service = DeepfakeService()

@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_active_user)
):
    """
    Upload video/image and run deepfake detection with real trained model.
    
    - **file**: Video or image file (mp4, mov, avi, jpg, png)
    
    Returns structured JSON with deepfake analysis results.
    """
    session_id = str(uuid.uuid4())
    temp_file_path = None
    
    try:
        logger.info(f"[DEEPFAKE] File received: {file.filename} ({file.content_type})")
        
        # Validate file type
        allowed_video = ["video/mp4", "video/avi", "video/quicktime", "video/x-msvideo"]
        allowed_image = ["image/jpeg", "image/png", "image/jpg"]
        
        is_video = file.content_type in allowed_video
        is_image = file.content_type in allowed_image
        
        if not (is_video or is_image):
            logger.warning(f"[DEEPFAKE] Invalid file type: {file.content_type}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Only video (mp4, mov, avi) and image (jpg, png) files are supported"
                }
            )
        
        # Validate file size (max 100MB)
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"[DEEPFAKE] File size: {file_size_mb:.2f} MB")
        
        if len(content) > 100 * 1024 * 1024:  # 100MB
            logger.warning(f"[DEEPFAKE] File too large: {file_size_mb:.2f} MB")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed (100 MB)"
                }
            )
        
        # Save to temporary file
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"[DEEPFAKE] Temporary file created: {temp_file_path}")
        
        # Run analysis based on file type
        if is_video:
            logger.info("[DEEPFAKE] Analyzing video...")
            analysis_result = service.analyze_video(temp_file_path)
        else:
            logger.info("[DEEPFAKE] Analyzing image...")
            # Convert file to base64 for image analysis
            import base64
            base64_content = base64.b64encode(content).decode('utf-8')
            analysis_result = service.analyze_image(base64_content)
        
        if "error" in analysis_result:
            logger.error(f"[DEEPFAKE] Analysis failed: {analysis_result['error']}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Deepfake analysis failed: {analysis_result['error']}"
                }
            )
        
        # Save to database if user is authenticated
        if current_user:
            logger.info("[DEEPFAKE] Saving results to database...")
            try:
                session = await prisma.verificationSession.create({
                    "userId": current_user["id"],
                    "selfiePath": file.filename,
                    "deepfakeScore": analysis_result.get("deepfake_score", 0.0),
                    "decision": analysis_result.get("decision", "UNKNOWN")
                })
                session_id = session["id"]
                
                await prisma.featureResult.create({
                    "sessionId": session_id,
                    "featureName": "deepfake",
                    "score": analysis_result.get("deepfake_score", 0.0),
                    "metadata": analysis_result
                })
                
                logger.info(f"[DEEPFAKE] Results saved to database - Session ID: {session_id}")
            except Exception as db_error:
                logger.error(f"[DEEPFAKE] Database error: {str(db_error)}")
                # Continue even if DB fails
        else:
            logger.info("[DEEPFAKE] Running in demo mode (no authentication)")
        
        logger.info(f"[DEEPFAKE] Analysis complete - Processing time: {analysis_result.get('processing_time_ms', 0)} ms")
        
        # Return structured response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "sessionId": session_id,
                "deepfakeScore": analysis_result.get("deepfake_score", 0.0),
                "decision": analysis_result.get("decision", "UNKNOWN"),
                "isDeepfake": analysis_result.get("is_deepfake", False),
                "confidence": analysis_result.get("confidence_level", 0.0),
                "framesAnalyzed": analysis_result.get("frames_analyzed", 0),
                "statistics": analysis_result.get("statistics", {}),
                "processingTimeMs": analysis_result.get("processing_time_ms", 0),
                "modelVersion": analysis_result.get("model_version", "unknown"),
                "device": analysis_result.get("device", "unknown"),
                "timestamp": analysis_result.get("timestamp", datetime.utcnow().isoformat())
            }
        )
        
    except HTTPException as he:
        logger.error(f"[DEEPFAKE] HTTP Exception: {str(he)}")
        return JSONResponse(
            status_code=he.status_code,
            content={
                "success": False,
                "error": he.detail
            }
        )
    except Exception as e:
        logger.error(f"[DEEPFAKE] Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }
        )
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"[DEEPFAKE] Temporary file deleted: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"[DEEPFAKE] Failed to delete temp file: {cleanup_error}")

@router.get("/info")
async def get_service_info():
    """Get information about the deepfake detection service."""
    return service.get_model_info()

@router.get("/health")
async def health_check():
    """Health check endpoint for service monitoring."""
    try:
        model_info = service.get_model_info()
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "deepfake_detection",
                "model_loaded": model_info.get("model_loaded", False),
                "device": model_info.get("device", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"[DEEPFAKE] Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
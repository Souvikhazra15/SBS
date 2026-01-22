"""
Deepfake Detection API Routes

RESTful endpoints for synthetic media and deepfake detection.
Supports both image and video analysis with advanced AI models.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.schemas.feature import DeepfakeRequest, FeatureRunResponse
from src.services.deepfake_service import DeepfakeService
from src.utils.auth import get_current_active_user
from src.config.prisma import prisma

router = APIRouter(prefix="/deepfake", tags=["Deepfake Detection"])
service = DeepfakeService()

@router.post("/run", response_model=FeatureRunResponse)
async def run_deepfake_detection(
    deepfake_request: DeepfakeRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Run deepfake detection on uploaded media file.
    
    - **media_file**: Base64 encoded image or video file
    - **media_type**: Type of media ('image' or 'video')
    
    Returns detailed deepfake analysis including:
    - Deepfake probability score (0-100)
    - Authenticity confidence level
    - Artifact detection results
    - Frame-by-frame analysis (for videos)
    """
    try:
        # Validate media type
        if deepfake_request.media_type.lower() not in ["image", "video"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Media type must be 'image' or 'video'"
            )
        
        # Run deepfake analysis
        analysis_result = service.analyze_media(
            deepfake_request.media_file,
            deepfake_request.media_type
        )
        
        if "error" in analysis_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Deepfake analysis failed: {analysis_result['error']}"
            )
        
        # Create verification session
        session_data = {
            "userId": current_user["id"],
            "deepfakeScore": analysis_result["deepfake_score"]
        }
        
        # Add media path based on type
        if deepfake_request.media_type.lower() == "image":
            session_data["selfiePath"] = "base64_media"
        
        session = await prisma.verificationsession.create(session_data)
        
        # Store feature result
        await prisma.featureresult.create({
            "sessionId": session.id,
            "featureName": "deepfake",
            "score": analysis_result["deepfake_score"],
            "metadata": analysis_result
        })
        
        return FeatureRunResponse(
            session_id=session.id,
            feature_name="deepfake",
            score=analysis_result["deepfake_score"],
            metadata=analysis_result,
            processing_time_ms=analysis_result.get("processing_time_ms"),
            status="completed",
            created_at=session.createdAt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{session_id}", response_model=FeatureRunResponse)
async def get_deepfake_result(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Retrieve deepfake detection results for a specific session.
    
    - **session_id**: UUID of the verification session
    
    Returns stored deepfake analysis results including scores and detailed metadata.
    """
    try:
        feature_result = await prisma.featureresult.find_first(
            where={
                "sessionId": session_id,
                "featureName": "deepfake",
                "session": {
                    "userId": current_user["id"]
                }
            },
            include={
                "session": True
            }
        )
        
        if not feature_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deepfake detection result not found for this session"
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

@router.post("/upload", response_model=Dict[str, Any])
async def upload_media_file(
    file: UploadFile = File(..., description="Image or video file for analysis"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload media file for deepfake detection.
    
    - **file**: Image or video file (JPEG, PNG, MP4, AVI, MOV)
    
    Returns deepfake analysis results for the uploaded media.
    """
    try:
        # Determine media type from file
        content_type = file.content_type
        if content_type.startswith("image/"):
            media_type = "image"
        elif content_type.startswith("video/"):
            media_type = "video"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image and video files are supported"
            )
        
        # Validate file size
        content = await file.read()
        max_size = 50 * 1024 * 1024 if media_type == "video" else 10 * 1024 * 1024  # 50MB for video, 10MB for image
        
        if len(content) > max_size:
            max_size_mb = max_size // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum {max_size_mb}MB allowed for {media_type}"
            )
        
        # Convert to base64 for processing
        import base64
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Run deepfake analysis
        analysis_result = service.analyze_media(base64_content, media_type)
        
        if "error" in analysis_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Deepfake analysis failed: {analysis_result['error']}"
            )
        
        # Create session and store results
        session_data = {
            "userId": current_user["id"],
            "deepfakeScore": analysis_result["deepfake_score"]
        }
        
        if media_type == "image":
            session_data["selfiePath"] = file.filename
        
        session = await prisma.verificationsession.create(session_data)
        
        await prisma.featureresult.create({
            "sessionId": session.id,
            "featureName": "deepfake",
            "score": analysis_result["deepfake_score"],
            "metadata": analysis_result
        })
        
        return {
            "session_id": session.id,
            "filename": file.filename,
            "media_type": media_type,
            "file_size": len(content),
            "analysis_result": analysis_result,
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/batch-analyze", response_model=List[Dict[str, Any]])
async def batch_deepfake_analysis(
    files: List[UploadFile] = File(..., description="Multiple media files for batch analysis"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Analyze multiple media files for deepfake content in batch.
    
    - **files**: List of image/video files (max 10 files)
    
    Returns array of analysis results for each file.
    """
    try:
        # Limit batch size
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 files allowed in batch analysis"
            )
        
        results = []
        
        for file in files:
            try:
                # Determine media type
                content_type = file.content_type
                if content_type.startswith("image/"):
                    media_type = "image"
                elif content_type.startswith("video/"):
                    media_type = "video"
                else:
                    results.append({
                        "filename": file.filename,
                        "error": "Unsupported file type",
                        "status": "failed"
                    })
                    continue
                
                # Read and validate file
                content = await file.read()
                max_size = 20 * 1024 * 1024  # 20MB limit for batch processing
                
                if len(content) > max_size:
                    results.append({
                        "filename": file.filename,
                        "error": "File too large for batch processing (max 20MB)",
                        "status": "failed"
                    })
                    continue
                
                # Convert to base64 and analyze
                import base64
                base64_content = base64.b64encode(content).decode('utf-8')
                
                analysis_result = service.analyze_media(base64_content, media_type)
                
                if "error" in analysis_result:
                    results.append({
                        "filename": file.filename,
                        "error": analysis_result["error"],
                        "status": "failed"
                    })
                    continue
                
                # Create session (simplified for batch)
                session = await prisma.verificationsession.create({
                    "userId": current_user["id"],
                    "deepfakeScore": analysis_result["deepfake_score"]
                })
                
                await prisma.featureresult.create({
                    "sessionId": session.id,
                    "featureName": "deepfake",
                    "score": analysis_result["deepfake_score"],
                    "metadata": analysis_result
                })
                
                results.append({
                    "filename": file.filename,
                    "session_id": session.id,
                    "media_type": media_type,
                    "deepfake_score": analysis_result["deepfake_score"],
                    "is_deepfake": analysis_result["is_deepfake"],
                    "confidence": analysis_result["confidence_level"],
                    "status": "completed"
                })
                
            except Exception as file_error:
                results.append({
                    "filename": file.filename,
                    "error": str(file_error),
                    "status": "failed"
                })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )

@router.get("/info")
async def get_service_info():
    """
    Get information about the deepfake detection service.
    
    Returns model capabilities, supported formats, and detection features.
    """
    return {
        "service_name": "Deepfake Detection",
        **service.get_model_info(),
        "capabilities": [
            "Image deepfake detection",
            "Video deepfake detection",
            "Facial artifact analysis",
            "Temporal consistency checking",
            "Generation artifact detection",
            "Pixel-level analysis",
            "Frequency domain analysis"
        ],
        "detection_methods": [
            "Neural network analysis",
            "Facial landmark consistency",
            "Skin texture analysis",
            "Eye reflection validation",
            "Motion pattern analysis",
            "Lip-sync accuracy",
            "Compression artifact detection"
        ]
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    """
    return {
        "status": "healthy",
        "service": "deepfake_detection",
        "timestamp": datetime.utcnow().isoformat(),
        "version": service.model_version
    }

"""
Face Matching API Routes

RESTful endpoints for facial recognition and biometric verification.
Provides face matching with liveness detection capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.schemas.feature import FaceMatchingRequest, FeatureRunResponse
from src.services.face_matching_service import FaceMatchingService
from src.utils.auth import get_current_active_user
from src.config.prisma import prisma

router = APIRouter(prefix="/face-matching", tags=["Face Matching"])
service = FaceMatchingService()

@router.post("/run", response_model=FeatureRunResponse)
async def run_face_matching(
    face_request: FaceMatchingRequest,
    enable_liveness: bool = True,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Run face matching between document and selfie images.
    
    - **document_image**: Base64 encoded document photo
    - **selfie_image**: Base64 encoded selfie/live capture
    - **enable_liveness**: Whether to perform liveness detection
    
    Returns detailed face matching results including:
    - Match score (0-100)
    - Liveness detection results
    - Biometric quality assessment
    - Anti-spoofing analysis
    """
    try:
        # Run face matching analysis
        match_result = service.match_faces(
            face_request.document_image,
            face_request.selfie_image,
            enable_liveness
        )
        
        if "error" in match_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face matching failed: {match_result['error']}"
            )
        
        # Create or update verification session
        session = await prisma.verificationsession.create({
            "userId": current_user["id"],
            "documentPath": "base64_document",
            "selfiePath": "base64_selfie",
            "faceMatchScore": match_result["face_match_score"]
        })
        
        # Store feature result
        await prisma.featureresult.create({
            "sessionId": session.id,
            "featureName": "face_matching",
            "score": match_result["face_match_score"],
            "metadata": match_result
        })
        
        return FeatureRunResponse(
            session_id=session.id,
            feature_name="face_matching",
            score=match_result["face_match_score"],
            metadata=match_result,
            processing_time_ms=match_result.get("processing_time_ms"),
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
async def get_face_matching_result(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Retrieve face matching results for a specific session.
    
    - **session_id**: UUID of the verification session
    
    Returns stored face matching analysis including match scores and liveness results.
    """
    try:
        feature_result = await prisma.featureresult.find_first(
            where={
                "sessionId": session_id,
                "featureName": "face_matching",
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
                detail="Face matching result not found for this session"
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
async def upload_face_images(
    document_file: UploadFile = File(..., description="Document image with face"),
    selfie_file: UploadFile = File(..., description="Selfie/live capture image"),
    enable_liveness: bool = Form(True, description="Enable liveness detection"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload both document and selfie images for face matching.
    
    - **document_file**: Document image file containing face
    - **selfie_file**: Selfie or live capture image file
    - **enable_liveness**: Whether to perform liveness detection
    
    Returns face matching analysis results.
    """
    try:
        # Validate both files
        for file in [document_file, selfie_file]:
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} must be an image"
                )
        
        # Read and convert files to base64
        import base64
        
        doc_content = await document_file.read()
        selfie_content = await selfie_file.read()
        
        # Validate file sizes (max 5MB each)
        for content, filename in [(doc_content, document_file.filename), 
                                (selfie_content, selfie_file.filename)]:
            if len(content) > 5 * 1024 * 1024:  # 5MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {filename} too large. Maximum 5MB allowed"
                )
        
        doc_base64 = base64.b64encode(doc_content).decode('utf-8')
        selfie_base64 = base64.b64encode(selfie_content).decode('utf-8')
        
        # Run face matching
        match_result = service.match_faces(doc_base64, selfie_base64, enable_liveness)
        
        if "error" in match_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face matching failed: {match_result['error']}"
            )
        
        # Create session and store results
        session = await prisma.verificationsession.create({
            "userId": current_user["id"],
            "documentPath": document_file.filename,
            "selfiePath": selfie_file.filename,
            "faceMatchScore": match_result["face_match_score"]
        })
        
        await prisma.featureresult.create({
            "sessionId": session.id,
            "featureName": "face_matching",
            "score": match_result["face_match_score"],
            "metadata": match_result
        })
        
        return {
            "session_id": session.id,
            "document_file": document_file.filename,
            "selfie_file": selfie_file.filename,
            "analysis_result": match_result,
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/liveness-only", response_model=Dict[str, Any])
async def run_liveness_detection_only(
    selfie_image: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Run liveness detection only on a selfie image.
    
    - **selfie_image**: Base64 encoded selfie image
    
    Returns liveness detection results without face matching.
    """
    try:
        # Decode image for liveness detection
        import base64
        import io
        import numpy as np
        from PIL import Image
        
        if selfie_image.startswith('data:image'):
            selfie_image = selfie_image.split(',')[1]
        
        image_bytes = base64.b64decode(selfie_image)
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        
        # Run liveness detection
        liveness_result = service._detect_liveness(image_array)
        
        return {
            "liveness_result": liveness_result,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Liveness detection failed: {str(e)}"
        )

@router.get("/info")
async def get_service_info():
    """
    Get information about the face matching service.
    
    Returns model capabilities, thresholds, and supported features.
    """
    return {
        "service_name": "Face Matching & Liveness Detection",
        **service.get_model_info(),
        "capabilities": [
            "Facial recognition and matching",
            "Liveness detection",
            "Anti-spoofing technology",
            "Biometric quality assessment",
            "3D face analysis"
        ],
        "liveness_features": [
            "Texture analysis",
            "Motion detection",
            "Challenge-response",
            "Print attack detection",
            "Screen attack detection",
            "Mask attack detection"
        ]
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    """
    return {
        "status": "healthy",
        "service": "face_matching",
        "timestamp": datetime.utcnow().isoformat(),
        "version": service.model_version
    }

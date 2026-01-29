"""
E-KYC API Routes

RESTful endpoints for e-KYC verification including document upload,
selfie capture, verification processing, and session history.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import Optional
import logging
import os
import tempfile
from pathlib import Path

from src.schemas.ekyc import (
    EkycSessionStartRequest,
    EkycSessionResponse,
    EkycRunRequest,
    EkycSessionHistoryResponse,
)
from src.services.ekyc_service import EkycService
from src.services.ocr_service import OCRService
from src.services.document_extractor import DocumentExtractor
from src.utils.auth import get_current_user
from src.config.prisma import get_db_pool

router = APIRouter(prefix="/e-kyc", tags=["E-KYC"])
logger = logging.getLogger(__name__)

# Initialize services
ocr_service = OCRService()
document_extractor = DocumentExtractor()


@router.post("/start")
async def start_ekyc_session():
    """
    Start a new e-KYC verification session
    
    - **No authentication required**
    - **Returns**: New e-KYC session with unique session ID
    
    Creates an anonymous session for document verification.
    """
    try:
        logger.info("[EKYC] Session start requested (anonymous)")
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
        session = await service.create_session(
            user_id=None,
            ip_address=None,
            user_agent=None,
        )
        
        logger.info(f"[EKYC] Session created: {session['sessionId']} (anonymous)")
        
        # Convert camelCase to snake_case for frontend
        return {
            "id": session["id"],
            "user_id": session.get("userId"),
            "session_id": session["sessionId"],
            "status": session["status"],
            "decision": session["decision"],
            "document_score": session.get("documentScore"),
            "face_match_score": session.get("faceMatchScore"),
            "liveness_score": session.get("livenessScore"),
            "overall_score": session.get("overallScore"),
            "rejection_reason": session.get("rejectionReason"),
            "review_notes": session.get("reviewNotes"),
            "created_at": session["createdAt"],
            "updated_at": session["updatedAt"],
            "completed_at": session.get("completedAt"),
            "documents": [],
            "results": []
        }
        
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
    document_image: UploadFile = File(...)
):
    """
    Upload identity document and extract data using OCR
    
    - **No authentication required**
    - **session_id**: E-KYC session ID
    - **document_type**: Type of document (AADHAAR, PAN_CARD, DRIVERS_LICENSE)
    - **document_image**: Image of document
    
    Returns extracted document details and OCR results.
    """
    try:
        logger.info(f"[EKYC] upload received for session: {session_id}, doc type: {document_type}")
        
        # Validate document type
        valid_types = ["AADHAAR", "PAN_CARD", "DRIVERS_LICENSE"]
        if document_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
            )
        
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
        # Verify session exists
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Read image data
        image_data = await document_image.read()
        logger.info(f"[EKYC] Image received: {len(image_data)} bytes")
        
        # Save to temp file for OCR processing
        temp_dir = Path(tempfile.gettempdir()) / "ekyc_uploads"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / f"{session_id}_{document_type}.jpg"
        
        with open(temp_file, "wb") as f:
            f.write(image_data)
        
        image_path = str(temp_file)
        logger.info(f"[EKYC] Image saved to: {image_path}")
        
        # Process OCR (this returns extracted data immediately)
        logger.info("[OCR] started")
        ocr_result = await extract_document_data(
            document_type=document_type,
            image_path=image_path,
            image_data=image_data
        )
        logger.info(f"[OCR] completed with confidence: {ocr_result['confidence']}")
        
        # Save document to database with extracted data
        async with db_pool.acquire() as conn:
            import uuid
            from datetime import datetime
            
            document_id = str(uuid.uuid4())
            
            # Build extracted data JSON
            extracted_json = {
                "extractedFields": ocr_result.get("extractedFields", {}),
                "confidence": ocr_result.get("confidence", 0.0),
                "rawText": ocr_result.get("rawText", "")
            }
            
            # Get document number based on type
            doc_number = None
            if document_type == "AADHAAR":
                doc_number = ocr_result.get("aadhaarNumber", "")
            elif document_type == "PAN_CARD":
                doc_number = ocr_result.get("panNumber", "")
            elif document_type == "DRIVERS_LICENSE":
                doc_number = ocr_result.get("licenseNumber", "")
            
            import json
            await conn.execute(
                '''
                INSERT INTO "ekyc_documents" 
                (id, "sessionId", type, "frontImageUrl", "documentNumber", "fullName", 
                 "dateOfBirth", "isAuthentic", "confidenceScore", "tamperingDetected",
                 "extractedData", "uploadedAt", "processedAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ''',
                document_id,
                session['id'],
                document_type,
                image_path,
                doc_number or "Not extracted",
                ocr_result.get("name"),
                ocr_result.get("dateOfBirth"),
                ocr_result.get("confidence", 0) > 0.5,
                ocr_result.get("confidence", 0),
                False,
                json.dumps(extracted_json),
                datetime.utcnow(),
                datetime.utcnow()
            )
            
            # Update session status
            await conn.execute(
                '''
                UPDATE "ekyc_sessions" 
                SET status = $1, "documentScore" = $2, "updatedAt" = $3 
                WHERE id = $4
                ''',
                "DOCUMENT_UPLOADED",
                ocr_result.get("confidence", 0) * 100,
                datetime.utcnow(),
                session['id']
            )
        
        logger.info(f"[DB] ekyc_document saved: {document_id}")
        logger.info(f"[EKYC] Document upload complete for session: {session_id}")
        
        return {
            "success": True,
            "message": "Document processed successfully",
            "documentId": document_id,
            "documentType": document_type,
            "extractedFields": ocr_result.get("extractedFields", {}),
            "confidence": ocr_result.get("confidence", 0.0),
            "name": ocr_result.get("name"),
            "dateOfBirth": ocr_result.get("dateOfBirth"),
            "documentNumber": doc_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Failed to upload document: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


async def extract_document_data(document_type: str, image_path: str, image_data: bytes) -> dict:
    """Helper function to extract document data using OCR"""
    try:
        # Run OCR
        if ocr_service.ocr is not None:
            result = ocr_service.ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                logger.warning("[OCR] No text detected in image")
                return {
                    "documentType": document_type,
                    "confidence": 0.0,
                    "error": "No text detected",
                    "extractedFields": {}
                }
            
            # Extract text
            text_lines = []
            for line in result[0]:
                text = line[1][0]
                text_lines.append(text)
            
            full_text = "\n".join(text_lines)
            logger.info(f"[OCR] Extracted {len(text_lines)} lines of text")
            
            # Extract document-specific fields
            extraction_result = document_extractor.extract(document_type, full_text, result[0])
            return extraction_result
        else:
            logger.warning("[OCR] OCR service not available")
            return {
                "documentType": document_type,
                "confidence": 0.0,
                "error": "OCR service not available",
                "extractedFields": {}
            }
    except Exception as e:
        logger.error(f"[OCR] Extraction failed: {str(e)}")
        return {
            "documentType": document_type,
            "confidence": 0.0,
            "error": str(e),
            "extractedFields": {}
        }


@router.post("/extract")
async def extract_document_fields(
    session_id: str = Form(...),
    document_type: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Re-extract fields from already uploaded document
    
    - **Requires**: JWT authentication
    - **session_id**: E-KYC session ID
    - **document_type**: Document type to re-process
    """
    try:
        logger.info(f"[EKYC] Re-extraction requested for session: {session_id}")
        
        db_pool = get_db_pool()
        async with db_pool.acquire() as conn:
            # Get session and document
            session = await conn.fetchrow(
                'SELECT * FROM "ekyc_sessions" WHERE "sessionId" = $1 AND "userId" = $2',
                session_id,
                current_user["id"]
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Get document
            document = await conn.fetchrow(
                'SELECT * FROM "ekyc_documents" WHERE "sessionId" = $1 AND type = $2 ORDER BY "uploadedAt" DESC LIMIT 1',
                session['id'],
                document_type
            )
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            # Read image from path
            image_path = document['frontImageUrl']
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Re-run OCR
            ocr_result = await extract_document_data(document_type, image_path, image_data)
            
            return {
                "success": True,
                "extractedFields": ocr_result.get("extractedFields", {}),
                "confidence": ocr_result.get("confidence", 0.0)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Re-extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get e-KYC session details with documents and results
    
    - **Requires**: JWT authentication
    - **session_id**: E-KYC session ID
    """
    try:
        logger.info(f"[EKYC] Session details requested: {session_id}")
        
        db_pool = get_db_pool()
        async with db_pool.acquire() as conn:
            # Get session
            session = await conn.fetchrow(
                'SELECT * FROM "ekyc_sessions" WHERE "sessionId" = $1 AND "userId" = $2',
                session_id,
                current_user["id"]
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Get documents
            documents = await conn.fetch(
                'SELECT * FROM "ekyc_documents" WHERE "sessionId" = $1 ORDER BY "uploadedAt" DESC',
                session['id']
            )
            
            # Get results
            results = await conn.fetch(
                'SELECT * FROM "ekyc_results" WHERE "sessionId" = $1 ORDER BY "processedAt" DESC',
                session['id']
            )
            
            return {
                "session": dict(session),
                "documents": [dict(d) for d in documents],
                "results": [dict(r) for r in results]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EKYC] Failed to get session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload-selfie")
async def upload_selfie(
    session_id: str = Form(...),
    selfie_image: UploadFile = File(...)
):
    """
    Upload selfie image to e-KYC session
    
    - **No authentication required**
    - **session_id**: E-KYC session ID
    - **selfie_image**: Selfie/video capture image
    
    Returns upload confirmation.
    """
    try:
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
        # Verify session exists
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # In production, upload to cloud storage
        selfie_url = f"/uploads/selfies/{session_id}_selfie.jpg"
        
        logger.info(f"[EKYC] Selfie uploaded for session: {session_id}")
        
        await service.upload_selfie(
            session_id=session['id'],
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


@router.post("/face-match")
async def match_faces(
    session_id: str = Form(...),
    id_image: UploadFile = File(...),
    selfie_image: UploadFile = File(...)
):
    """
    Perform face matching between ID document and selfie
    
    - **No authentication required**
    - **session_id**: E-KYC session ID
    - **id_image**: ID document image containing face
    - **selfie_image**: Selfie/webcam capture image
    
    Returns face matching results with similarity score and decision.
    """
    try:
        logger.info(f"[FACE-MATCH] Request received for session: {session_id}")
        
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
        # Verify session exists
        session = await service.get_session(session_id)
        if not session:
            logger.warning(f"[FACE-MATCH] Session not found: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Read images
        logger.info("[FACE-MATCH] Reading images...")
        id_image_data = await id_image.read()
        selfie_image_data = await selfie_image.read()
        
        logger.info(f"[FACE-MATCH] ID image size: {len(id_image_data)} bytes")
        logger.info(f"[FACE-MATCH] Selfie image size: {len(selfie_image_data)} bytes")
        
        # Import face matching service
        from src.services.face_matching_service import get_face_matching_service
        
        face_service = get_face_matching_service()
        
        # Perform face matching
        logger.info("[FACE-MATCH] Running face detection and matching...")
        match_result = face_service.match_faces(
            id_image_bytes=id_image_data,
            selfie_image_bytes=selfie_image_data
        )
        
        logger.info(f"[FACE-MATCH] Result: {match_result['decision']}, Score: {match_result['similarity_score']:.4f}")
        
        # Save result to database
        async with db_pool.acquire() as conn:
            import uuid
            from datetime import datetime
            
            result_id = str(uuid.uuid4())
            
            await conn.execute(
                '''
                INSERT INTO "face_match_results"
                (id, "sessionId", "idFaceDetected", "selfieFaceDetected", 
                 "idFaceCount", "selfieFaceCount", "similarityScore", decision,
                 threshold, "modelName", "modelVersion", "processingTime",
                 error, "errorCode", "createdAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ''',
                result_id,
                session['id'],
                match_result['id_face_detected'],
                match_result['selfie_face_detected'],
                match_result['id_face_count'],
                match_result['selfie_face_count'],
                match_result['similarity_score'],
                match_result['decision'],
                match_result['threshold'],
                'insightface',
                'buffalo_l',
                match_result['processing_time'],
                match_result.get('error'),
                match_result['decision'] if match_result.get('error') else None,
                datetime.utcnow()
            )
            
            # Update session with face match score
            if match_result['decision'] == 'MATCH':
                face_match_score = match_result['similarity_score'] * 100
                await conn.execute(
                    '''
                    UPDATE "ekyc_sessions"
                    SET "faceMatchScore" = $1, "updatedAt" = $2
                    WHERE id = $3
                    ''',
                    face_match_score,
                    datetime.utcnow(),
                    session['id']
                )
                logger.info(f"[FACE-MATCH] Updated session with score: {face_match_score:.2f}")
        
        # Return error if face matching failed
        if match_result['decision'] != 'MATCH':
            logger.warning(f"[FACE-MATCH] Face match failed: {match_result['decision']}")
            return {
                "success": False,
                "decision": match_result['decision'],
                "similarity_score": match_result['similarity_score'],
                "threshold": match_result['threshold'],
                "error": match_result.get('error', 'Face does not match'),
                "error_code": match_result['decision'],
                "id_face_detected": match_result['id_face_detected'],
                "selfie_face_detected": match_result['selfie_face_detected'],
                "processing_time": match_result['processing_time']
            }
        
        # Success case
        logger.info(f"[FACE-MATCH] ✓ Match successful for session: {session_id}")
        return {
            "success": True,
            "decision": match_result['decision'],
            "similarity_score": match_result['similarity_score'],
            "threshold": match_result['threshold'],
            "id_face_detected": match_result['id_face_detected'],
            "selfie_face_detected": match_result['selfie_face_detected'],
            "processing_time": match_result['processing_time'],
            "message": "Faces matched successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FACE-MATCH] Failed to match faces: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match faces: {str(e)}"
        )


@router.post("/run", response_model=EkycSessionResponse)
async def run_ekyc_verification(
    request: EkycRunRequest
):
    """
    Run complete e-KYC verification process
    
    - **No authentication required**
    - **session_id**: E-KYC session ID to process
    
    Returns verification results including:
    - Document authenticity score
    - Face matching score
    - Liveness detection score
    - Overall score
    - Final decision (APPROVED/REJECTED/REVIEW_REQUIRED)
    """
    try:
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
        # Verify session exists
        session = await service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"[EKYC] Running verification for session: {request.session_id}")
        
        result = await service.run_verification(session['id'])
        
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
    session_id: str
):
    """
    Get e-KYC session details by ID
    
    - **No authentication required**
    - **session_id**: E-KYC session ID
    
    Returns session with all documents and verification results.
    """
    try:
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
        session = await service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
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
        db_pool = get_db_pool()
        service = EkycService(db_pool)
        
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

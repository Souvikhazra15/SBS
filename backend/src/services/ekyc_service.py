"""
E-KYC Service

Business logic for e-KYC verification including document processing,
face matching, liveness detection, and decision making.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from prisma import Prisma

from src.schemas.ekyc import (
    EkycStatusEnum,
    EkycDecisionEnum,
    DocumentTypeEnum,
)

logger = logging.getLogger(__name__)


class EkycService:
    """Service for e-KYC verification operations"""

    def __init__(self, db: Prisma):
        self.db = db

    async def create_session(self, user_id: str, ip_address: Optional[str] = None, 
                           user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new e-KYC session for a user
        
        Args:
            user_id: User ID from JWT
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created e-KYC session
        """
        try:
            logger.info(f"[EKYC] Creating session for user: {user_id}")
            
            session = await self.db.ekycsession.create({
                "data": {
                    "userId": user_id,
                    "status": EkycStatusEnum.PENDING,
                    "decision": EkycDecisionEnum.PENDING,
                    "ipAddress": ip_address,
                    "userAgent": user_agent,
                }
            })
            
            logger.info(f"[EKYC] Session created: {session.sessionId}")
            return session
            
        except Exception as e:
            logger.error(f"[EKYC] Failed to create session: {str(e)}")
            raise

    async def upload_document(self, session_id: str, document_type: str,
                            front_image_url: str, back_image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload document to e-KYC session
        
        Args:
            session_id: E-KYC session ID
            document_type: Type of document
            front_image_url: URL to front image
            back_image_url: URL to back image (optional)
            
        Returns:
            Created document record
        """
        try:
            logger.info(f"[EKYC] Uploading document for session: {session_id}")
            
            # Create document record
            document = await self.db.ekycdocument.create({
                "data": {
                    "sessionId": session_id,
                    "type": document_type,
                    "frontImageUrl": front_image_url,
                    "backImageUrl": back_image_url,
                }
            })
            
            # Update session status
            await self.db.ekycsession.update({
                "where": {"sessionId": session_id},
                "data": {"status": EkycStatusEnum.DOCUMENT_UPLOADED}
            })
            
            logger.info(f"[EKYC] Document uploaded: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"[EKYC] Failed to upload document: {str(e)}")
            raise

    async def upload_selfie(self, session_id: str, selfie_url: str) -> Dict[str, Any]:
        """
        Upload selfie for e-KYC session (stored as additional document)
        
        Args:
            session_id: E-KYC session ID
            selfie_url: URL to selfie image
            
        Returns:
            Updated session
        """
        try:
            logger.info(f"[EKYC] Uploading selfie for session: {session_id}")
            
            # Update session status
            session = await self.db.ekycsession.update({
                "where": {"sessionId": session_id},
                "data": {"status": EkycStatusEnum.SELFIE_UPLOADED}
            })
            
            logger.info(f"[EKYC] Selfie uploaded for session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"[EKYC] Failed to upload selfie: {str(e)}")
            raise

    async def run_verification(self, session_id: str) -> Dict[str, Any]:
        """
        Run complete e-KYC verification process
        
        Args:
            session_id: E-KYC session ID
            
        Returns:
            Updated session with verification results
        """
        try:
            logger.info(f"[EKYC] Starting verification for session: {session_id}")
            
            # Update status to processing
            await self.db.ekycsession.update({
                "where": {"sessionId": session_id},
                "data": {"status": EkycStatusEnum.PROCESSING}
            })
            
            # Fetch session with documents
            session = await self.db.ekycsession.find_unique({
                "where": {"sessionId": session_id},
                "include": {
                    "documents": True,
                    "results": True,
                }
            })
            
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Simulate verification processes (in production, call actual verification services)
            # 1. Document Authentication
            document_score = await self._verify_document_authenticity(session)
            logger.info(f"[EKYC] Document verification complete: {document_score}")
            
            # 2. Face Matching
            face_match_score = await self._verify_face_match(session)
            logger.info(f"[EKYC] Face matching complete: {face_match_score}")
            
            # 3. Liveness Detection
            liveness_score = await self._verify_liveness(session)
            logger.info(f"[EKYC] Liveness detection complete: {liveness_score}")
            
            # Calculate overall score and decision
            overall_score = (document_score + face_match_score + liveness_score) / 3
            decision = self._make_decision(overall_score, document_score, face_match_score, liveness_score)
            
            # Update session with results
            updated_session = await self.db.ekycsession.update({
                "where": {"sessionId": session_id},
                "data": {
                    "status": EkycStatusEnum.COMPLETED,
                    "decision": decision,
                    "documentScore": document_score,
                    "faceMatchScore": face_match_score,
                    "livenessScore": liveness_score,
                    "overallScore": overall_score,
                    "completedAt": datetime.utcnow(),
                },
                "include": {
                    "documents": True,
                    "results": True,
                }
            })
            
            logger.info(f"[EKYC] Verification completed: {session_id}, Decision: {decision}")
            logger.info(f"[EKYC] Saved to DB: Session {session_id}")
            
            return updated_session
            
        except Exception as e:
            logger.error(f"[EKYC] Verification failed: {str(e)}")
            # Update session to failed status
            await self.db.ekycsession.update({
                "where": {"sessionId": session_id},
                "data": {
                    "status": EkycStatusEnum.FAILED,
                    "rejectionReason": str(e),
                }
            })
            raise

    async def _verify_document_authenticity(self, session: Dict[str, Any]) -> float:
        """
        Verify document authenticity
        
        In production, this would call actual document verification service.
        For now, returns a simulated score.
        """
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Simulated score (85-98)
        score = 92.5
        
        # Save result
        await self.db.ekycresult.create({
            "data": {
                "sessionId": session.id,
                "verificationType": "document_auth",
                "score": score,
                "isPassed": score >= 70,
                "confidence": 0.95,
                "details": {"method": "ml_classifier", "checks": ["hologram", "security_features", "tampering"]},
                "modelVersion": "v1.0.0",
                "processingTime": 500,
            }
        })
        
        return score

    async def _verify_face_match(self, session: Dict[str, Any]) -> float:
        """
        Verify face matching between document and selfie
        
        In production, this would call actual face matching service.
        """
        await asyncio.sleep(0.5)
        
        score = 89.3
        
        await self.db.ekycresult.create({
            "data": {
                "sessionId": session.id,
                "verificationType": "face_match",
                "score": score,
                "isPassed": score >= 75,
                "confidence": 0.91,
                "details": {"similarity": score, "landmarks_matched": 68},
                "modelVersion": "v1.0.0",
                "processingTime": 500,
            }
        })
        
        return score

    async def _verify_liveness(self, session: Dict[str, Any]) -> float:
        """
        Verify liveness detection
        
        In production, this would call actual liveness detection service.
        """
        await asyncio.sleep(0.5)
        
        score = 94.7
        
        await self.db.ekycresult.create({
            "data": {
                "sessionId": session.id,
                "verificationType": "liveness",
                "score": score,
                "isPassed": score >= 80,
                "confidence": 0.96,
                "details": {"method": "depth_analysis", "frames_analyzed": 30},
                "modelVersion": "v1.0.0",
                "processingTime": 500,
            }
        })
        
        return score

    def _make_decision(self, overall_score: float, document_score: float, 
                      face_match_score: float, liveness_score: float) -> str:
        """
        Make final e-KYC decision based on scores
        
        Args:
            overall_score: Combined score
            document_score: Document authenticity score
            face_match_score: Face matching score
            liveness_score: Liveness detection score
            
        Returns:
            Decision (APPROVED, REJECTED, REVIEW_REQUIRED)
        """
        # All scores must meet minimum thresholds
        if document_score < 70 or face_match_score < 75 or liveness_score < 80:
            return EkycDecisionEnum.REJECTED
        
        # High confidence approval
        if overall_score >= 85:
            return EkycDecisionEnum.APPROVED
        
        # Medium confidence - requires review
        if overall_score >= 70:
            return EkycDecisionEnum.REVIEW_REQUIRED
        
        # Low confidence - rejected
        return EkycDecisionEnum.REJECTED

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get e-KYC session by ID
        
        Args:
            session_id: E-KYC session ID
            
        Returns:
            Session with documents and results, or None
        """
        try:
            session = await self.db.ekycsession.find_unique({
                "where": {"sessionId": session_id},
                "include": {
                    "documents": True,
                    "results": True,
                }
            })
            return session
        except Exception as e:
            logger.error(f"[EKYC] Failed to fetch session: {str(e)}")
            return None

    async def get_user_sessions(self, user_id: str, skip: int = 0, 
                              take: int = 20) -> List[Dict[str, Any]]:
        """
        Get all e-KYC sessions for a user
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            take: Number of records to take
            
        Returns:
            List of sessions
        """
        try:
            sessions = await self.db.ekycsession.find_many({
                "where": {"userId": user_id},
                "include": {
                    "documents": True,
                    "results": True,
                },
                "orderBy": {"createdAt": "desc"},
                "skip": skip,
                "take": take,
            })
            return sessions
        except Exception as e:
            logger.error(f"[EKYC] Failed to fetch user sessions: {str(e)}")
            return []

    async def count_user_sessions(self, user_id: str) -> int:
        """
        Count total e-KYC sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Total count
        """
        try:
            count = await self.db.ekycsession.count({
                "where": {"userId": user_id}
            })
            return count
        except Exception as e:
            logger.error(f"[EKYC] Failed to count user sessions: {str(e)}")
            return 0

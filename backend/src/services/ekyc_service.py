"""
E-KYC Service

Business logic for e-KYC verification including document processing,
face matching, liveness detection, and decision making.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from src.schemas.ekyc import (
    EkycStatusEnum,
    EkycDecisionEnum,
    DocumentTypeEnum,
)

logger = logging.getLogger(__name__)


class EkycService:
    """Service for e-KYC verification operations"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

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
            
            session_id = str(uuid.uuid4())
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    '''
                    INSERT INTO "ekyc_sessions" 
                    (id, "userId", "sessionId", status, decision, "ipAddress", "userAgent", "createdAt", "updatedAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING *
                    ''',
                    str(uuid.uuid4()),
                    user_id,
                    session_id,
                    EkycStatusEnum.PENDING,
                    EkycDecisionEnum.PENDING,
                    ip_address,
                    user_agent,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                
                session = dict(result)
            
            logger.info(f"[EKYC] Session created: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"[EKYC] Failed to create session: {str(e)}")
            raise

    async def upload_document(self, session_id: str, document_type: str,
                            front_image_url: str, back_image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload document to e-KYC session
        
        Args:
            session_id: E-KYC session ID (internal DB ID, not sessionId field)
            document_type: Type of document
            front_image_url: URL to front image
            back_image_url: URL to back image (optional)
            
        Returns:
            Created document record
        """
        try:
            logger.info(f"[EKYC] Uploading document for session: {session_id}")
            
            async with self.db_pool.acquire() as conn:
                # Create document record
                document = await conn.fetchrow(
                    '''
                    INSERT INTO "ekyc_documents" 
                    (id, "sessionId", type, "frontImageUrl", "backImageUrl", "tamperingDetected", "uploadedAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    ''',
                    str(uuid.uuid4()),
                    session_id,
                    document_type,
                    front_image_url,
                    back_image_url,
                    False,
                    datetime.utcnow()
                )
                
                # Update session status
                await conn.execute(
                    '''
                    UPDATE "ekyc_sessions" 
                    SET status = $1, "updatedAt" = $2 
                    WHERE id = $3
                    ''',
                    EkycStatusEnum.DOCUMENT_UPLOADED,
                    datetime.utcnow(),
                    session_id
                )
            
            logger.info(f"[EKYC] Document uploaded: {document['id']}")
            return dict(document)
            
        except Exception as e:
            logger.error(f"[EKYC] Failed to upload document: {str(e)}")
            raise

    async def upload_selfie(self, session_id: str, selfie_url: str) -> Dict[str, Any]:
        """
        Upload selfie for e-KYC session (stored as additional document)
        
        Args:
            session_id: E-KYC session ID (internal DB ID)
            selfie_url: URL to selfie image
            
        Returns:
            Updated session
        """
        try:
            logger.info(f"[EKYC] Uploading selfie for session: {session_id}")
            
            async with self.db_pool.acquire() as conn:
                # Update session status
                session = await conn.fetchrow(
                    '''
                    UPDATE "ekyc_sessions" 
                    SET status = $1, "updatedAt" = $2 
                    WHERE id = $3
                    RETURNING *
                    ''',
                    EkycStatusEnum.SELFIE_UPLOADED,
                    datetime.utcnow(),
                    session_id
                )
            
            logger.info(f"[EKYC] Selfie uploaded for session: {session_id}")
            return dict(session)
            
        except Exception as e:
            logger.error(f"[EKYC] Failed to upload selfie: {str(e)}")
            raise

    async def run_verification(self, session_id: str) -> Dict[str, Any]:
        """
        Run complete e-KYC verification process
        
        Args:
            session_id: E-KYC session ID (internal DB ID)
            
        Returns:
            Updated session with verification results
        """
        try:
            logger.info(f"[EKYC] Starting verification for session: {session_id}")
            
            async with self.db_pool.acquire() as conn:
                # Update status to processing
                await conn.execute(
                    '''
                    UPDATE "ekyc_sessions" 
                    SET status = $1, "updatedAt" = $2 
                    WHERE id = $3
                    ''',
                    EkycStatusEnum.PROCESSING,
                    datetime.utcnow(),
                    session_id
                )
                
                # Fetch session
                session = await conn.fetchrow(
                    'SELECT * FROM "ekyc_sessions" WHERE id = $1',
                    session_id
                )
                
                if not session:
                    raise ValueError(f"Session not found: {session_id}")
                
                session_dict = dict(session)
            
            # Simulate verification processes (in production, call actual verification services)
            # 1. Document Authentication
            document_score = await self._verify_document_authenticity(session_dict)
            logger.info(f"[EKYC] Document verification complete: {document_score}")
            
            # 2. Face Matching
            face_match_score = await self._verify_face_match(session_dict)
            logger.info(f"[EKYC] Face matching complete: {face_match_score}")
            
            # 3. Liveness Detection
            liveness_score = await self._verify_liveness(session_dict)
            logger.info(f"[EKYC] Liveness detection complete: {liveness_score}")
            
            # Calculate overall score and decision
            overall_score = (document_score + face_match_score + liveness_score) / 3
            decision = self._make_decision(overall_score, document_score, face_match_score, liveness_score)
            
            # Update session with results
            async with self.db_pool.acquire() as conn:
                updated_session = await conn.fetchrow(
                    '''
                    UPDATE "ekyc_sessions" 
                    SET status = $1, decision = $2, "documentScore" = $3, 
                        "faceMatchScore" = $4, "livenessScore" = $5, "overallScore" = $6,
                        "completedAt" = $7, "updatedAt" = $8
                    WHERE id = $9
                    RETURNING *
                    ''',
                    EkycStatusEnum.COMPLETED,
                    decision,
                    document_score,
                    face_match_score,
                    liveness_score,
                    overall_score,
                    datetime.utcnow(),
                    datetime.utcnow(),
                    session_id
                )
            
            logger.info(f"[EKYC] Verification completed: {session_id}, Decision: {decision}")
            logger.info(f"[EKYC] Saved to DB: Session {session_id}")
            
            return dict(updated_session)
            
        except Exception as e:
            logger.error(f"[EKYC] Verification failed: {str(e)}")
            # Update session to failed status
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    '''
                    UPDATE "ekyc_sessions" 
                    SET status = $1, "rejectionReason" = $2, "updatedAt" = $3
                    WHERE id = $4
                    ''',
                    EkycStatusEnum.FAILED,
                    str(e),
                    datetime.utcnow(),
                    session_id
                )
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
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO "ekyc_results" 
                (id, "sessionId", "verificationType", score, "isPassed", confidence, details, "modelVersion", "processingTime", "processedAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''',
                str(uuid.uuid4()),
                session['id'],
                'document_auth',
                score,
                score >= 70,
                0.95,
                '{"method": "ml_classifier", "checks": ["hologram", "security_features", "tampering"]}',
                'v1.0.0',
                500,
                datetime.utcnow()
            )
        
        return score

    async def _verify_face_match(self, session: Dict[str, Any]) -> float:
        """
        Verify face matching between document and selfie
        
        In production, this would call actual face matching service.
        """
        await asyncio.sleep(0.5)
        
        score = 89.3
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO "ekyc_results" 
                (id, "sessionId", "verificationType", score, "isPassed", confidence, details, "modelVersion", "processingTime", "processedAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''',
                str(uuid.uuid4()),
                session['id'],
                'face_match',
                score,
                score >= 75,
                0.91,
                '{"similarity": ' + str(score) + ', "landmarks_matched": 68}',
                'v1.0.0',
                500,
                datetime.utcnow()
            )
        
        return score

    async def _verify_liveness(self, session: Dict[str, Any]) -> float:
        """
        Verify liveness detection
        
        In production, this would call actual liveness detection service.
        """
        await asyncio.sleep(0.5)
        
        score = 94.7
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO "ekyc_results" 
                (id, "sessionId", "verificationType", score, "isPassed", confidence, details, "modelVersion", "processingTime", "processedAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''',
                str(uuid.uuid4()),
                session['id'],
                'liveness',
                score,
                score >= 80,
                0.96,
                '{"method": "depth_analysis", "frames_analyzed": 30}',
                'v1.0.0',
                500,
                datetime.utcnow()
            )
        
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
        Get e-KYC session by sessionId field
        
        Args:
            session_id: E-KYC sessionId field value
            
        Returns:
            Session with documents and results, or None
        """
        try:
            async with self.db_pool.acquire() as conn:
                session = await conn.fetchrow(
                    'SELECT * FROM "ekyc_sessions" WHERE "sessionId" = $1',
                    session_id
                )
                
                if not session:
                    return None
                
                session_dict = dict(session)
                
                # Fetch documents
                documents = await conn.fetch(
                    'SELECT * FROM "ekyc_documents" WHERE "sessionId" = $1',
                    session_dict['id']
                )
                session_dict['documents'] = [dict(d) for d in documents]
                
                # Fetch results
                results = await conn.fetch(
                    'SELECT * FROM "ekyc_results" WHERE "sessionId" = $1',
                    session_dict['id']
                )
                session_dict['results'] = [dict(r) for r in results]
                
                return session_dict
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
            async with self.db_pool.acquire() as conn:
                sessions = await conn.fetch(
                    '''
                    SELECT * FROM "ekyc_sessions" 
                    WHERE "userId" = $1 
                    ORDER BY "createdAt" DESC 
                    LIMIT $2 OFFSET $3
                    ''',
                    user_id,
                    take,
                    skip
                )
                
                result = []
                for session in sessions:
                    session_dict = dict(session)
                    
                    # Fetch documents for each session
                    documents = await conn.fetch(
                        'SELECT * FROM "ekyc_documents" WHERE "sessionId" = $1',
                        session_dict['id']
                    )
                    session_dict['documents'] = [dict(d) for d in documents]
                    
                    # Fetch results for each session
                    results = await conn.fetch(
                        'SELECT * FROM "ekyc_results" WHERE "sessionId" = $1',
                        session_dict['id']
                    )
                    session_dict['results'] = [dict(r) for r in results]
                    
                    result.append(session_dict)
                
                return result
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
            async with self.db_pool.acquire() as conn:
                count = await conn.fetchval(
                    'SELECT COUNT(*) FROM "ekyc_sessions" WHERE "userId" = $1',
                    user_id
                )
                return count or 0
        except Exception as e:
            logger.error(f"[EKYC] Failed to count user sessions: {str(e)}")
            return 0
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

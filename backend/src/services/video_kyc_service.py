"""
Video KYC Service - Business logic for Video KYC verification
"""

import os
import base64
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
from src.schemas.video_kyc import (
    VideoKYCStatusEnum,
    VerificationDecisionEnum,
    VideoKYCSessionCreate,
    VideoKYCSessionUpdate,
    VideoKYCQuestionCreate,
    VideoKYCAnswerCreate,
    VideoKYCChatMessageCreate,
    VideoKYCVerificationResultCreate,
    MessageTypeEnum
)

logger = logging.getLogger(__name__)


class VideoKYCService:
    """Service for Video KYC verification operations"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.upload_dir = "uploads/video_kyc"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def create_session(self, user_id: str, ip_address: Optional[str] = None, 
                            user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Video KYC session"""
        
        try:
            logger.info(f"[VIDEO-KYC] Creating session for user: {user_id}")
            
            async with self.pool.acquire() as conn:
                session_id = f"vkyc_{os.urandom(16).hex()}"
                
                result = await conn.fetchrow('''
                    INSERT INTO video_kyc_sessions 
                    (id, "userId", "sessionStatus", "currentStep", "totalSteps", "ipAddress", "userAgent", 
                     "documentVerified", "faceMatched", "livenessChecked", "finalDecision", "sessionStartedAt", "createdAt", "updatedAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    RETURNING *
                ''', session_id, user_id, 'IDLE', 0, 8, ip_address, user_agent, False, False, False, 'PENDING',
                datetime.utcnow(), datetime.utcnow(), datetime.utcnow())
                
                session = dict(result)
            
            logger.info(f"[VIDEO-KYC] Session created: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to create session: {str(e)}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get Video KYC session by ID"""
        
        try:
            async with self.pool.acquire() as conn:
                session = await conn.fetchrow('''
                    SELECT * FROM video_kyc_sessions WHERE id = $1
                ''', session_id)
                
                if not session:
                    return None
                
                return dict(session)
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to get session: {str(e)}")
            raise

    async def update_session(self, session_id: str, 
                           update_data: VideoKYCSessionUpdate) -> Dict[str, Any]:
        """Update Video KYC session"""
        
        try:
            data_dict = update_data.dict(exclude_none=True)
            
            if not data_dict:
                return await self.get_session(session_id)
            
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            param_num = 1
            
            for key, value in data_dict.items():
                set_clauses.append(f'"{key}" = ${param_num}')
                values.append(value)
                param_num += 1
            
            # Add updatedAt
            set_clauses.append(f'"updatedAt" = ${param_num}')
            values.append(datetime.utcnow())
            param_num += 1
            
            # Add session_id for WHERE clause
            values.append(session_id)
            
            query = f'''
                UPDATE video_kyc_sessions 
                SET {", ".join(set_clauses)}
                WHERE id = ${param_num}
                RETURNING *
            '''
            
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(query, *values)
                return dict(result)
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to update session: {str(e)}")
            raise

    async def update_session_status(self, session_id: str, 
                                   status: VideoKYCStatusEnum) -> Dict[str, Any]:
        """Update session status"""
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('''
                    UPDATE video_kyc_sessions 
                    SET "sessionStatus" = $1, "updatedAt" = $2
                    WHERE id = $3
                    RETURNING *
                ''', status, datetime.utcnow(), session_id)
                
                return dict(result)
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to update session status: {str(e)}")
            raise

    async def add_question(self, question_data: VideoKYCQuestionCreate) -> Dict[str, Any]:
        """Add a question to Video KYC session"""
        
        try:
            async with self.pool.acquire() as conn:
                question_id = str(uuid.uuid4())
                
                result = await conn.fetchrow('''
                    INSERT INTO video_kyc_questions 
                    (id, "sessionId", "questionText", "questionType", "questionOrder", 
                     "validationRules", required, "createdAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING *
                ''', question_id, question_data.sessionId, question_data.questionText,
                question_data.questionType, question_data.questionOrder, question_data.validationRules,
                question_data.required, datetime.utcnow())
                
                return dict(result)
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to add question: {str(e)}")
            raise

    async def add_answer(self, answer_data: VideoKYCAnswerCreate) -> Dict[str, Any]:
        """Add an answer to a Video KYC question"""
        
        try:
            async with self.pool.acquire() as conn:
                answer_id = str(uuid.uuid4())
                
                # Create answer
                result = await conn.fetchrow('''
                    INSERT INTO video_kyc_answers 
                    (id, "sessionId", "questionId", "answerText", "answerType", 
                     "responseTime", "createdAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                ''', answer_id, answer_data.sessionId, answer_data.questionId,
                answer_data.answerText, answer_data.answerType, answer_data.responseTime,
                datetime.utcnow())
                
                answer = dict(result)
                
                # Get question to update session with answer
                question = await conn.fetchrow('''
                    SELECT * FROM video_kyc_questions WHERE id = $1
                ''', answer_data.questionId)
                
                if question:
                    question_type = question['questionType']
                    
                    field_map = {
                        "name": "name",
                        "dob": "dateOfBirth",
                        "address": "address",
                        "income": "income",
                        "employment": "employment",
                        "aadhar": "aadhar",
                        "pan": "pan",
                    }
                    
                    if question_type in field_map:
                        await conn.execute(f'''
                            UPDATE video_kyc_sessions 
                            SET "{field_map[question_type]}" = $1, "updatedAt" = $2
                            WHERE id = $3
                        ''', answer_data.answerText, datetime.utcnow(), answer_data.sessionId)
                
                return answer
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to add answer: {str(e)}")
            raise

    async def add_chat_message(self, message_data: VideoKYCChatMessageCreate) -> Dict[str, Any]:
        """Add a chat message to Video KYC session"""
        
        try:
            async with self.pool.acquire() as conn:
                message_id = str(uuid.uuid4())
                
                result = await conn.fetchrow('''
                    INSERT INTO video_kyc_chat_messages 
                    (id, "sessionId", "messageText", "messageType", timestamp, "createdAt")
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                ''', message_id, message_data.sessionId, message_data.messageText,
                message_data.messageType, datetime.utcnow(), datetime.utcnow())
                
                return dict(result)
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to add chat message: {str(e)}")
            raise

    async def save_uploaded_file(self, session_id: str, file_data: bytes, 
                                file_type: str, filename: str) -> str:
        """Save uploaded file and return file path"""
        
        try:
            session_dir = os.path.join(self.upload_dir, session_id)
            os.makedirs(session_dir, exist_ok=True)
            
            file_extension = os.path.splitext(filename)[1]
            file_path = os.path.join(session_dir, f"{file_type}{file_extension}")
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # Update session with file path
            field_map = {
                "profile": "profileImagePath",
                "signature": "signatureImagePath",
                "document": "documentImagePath",
            }
            
            if file_type in field_map:
                async with self.pool.acquire() as conn:
                    await conn.execute(f'''
                        UPDATE video_kyc_sessions 
                        SET "{field_map[file_type]}" = $1, "updatedAt" = $2
                        WHERE id = $3
                    ''', file_path, datetime.utcnow(), session_id)
            
            return file_path
            
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to save uploaded file: {str(e)}")
            raise

    async def add_verification_result(self, result_data: VideoKYCVerificationResultCreate) -> Dict[str, Any]:
        """Add a verification result to Video KYC session"""
        
        try:
            async with self.pool.acquire() as conn:
                result_id = str(uuid.uuid4())
                
                # Create verification result
                result = await conn.fetchrow('''
                    INSERT INTO video_kyc_verification_results 
                    (id, "sessionId", "verificationType", score, confidence, "isPassed", 
                     details, "modelVersion", "processingTime", "createdAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING *
                ''', result_id, result_data.sessionId, result_data.verificationType,
                result_data.score, result_data.confidence, result_data.isPassed,
                result_data.details, result_data.modelVersion, result_data.processingTime,
                datetime.utcnow())
                
                verification_result = dict(result)
                
                # Update session with verification scores
                update_fields = []
                update_values = []
                param_num = 1
                
                if result_data.verificationType == "document":
                    update_fields.append(f'"documentVerified" = ${param_num}')
                    update_values.append(result_data.isPassed)
                    param_num += 1
                    update_fields.append(f'"forgeryScore" = ${param_num}')
                    update_values.append(result_data.score)
                    param_num += 1
                elif result_data.verificationType == "face_match":
                    update_fields.append(f'"faceMatched" = ${param_num}')
                    update_values.append(result_data.isPassed)
                    param_num += 1
                    update_fields.append(f'"faceMatchScore" = ${param_num}')
                    update_values.append(result_data.score)
                    param_num += 1
                elif result_data.verificationType == "deepfake":
                    update_fields.append(f'"livenessChecked" = ${param_num}')
                    update_values.append(result_data.isPassed)
                    param_num += 1
                    update_fields.append(f'"deepfakeScore" = ${param_num}')
                    update_values.append(result_data.score)
                    param_num += 1
                elif result_data.verificationType == "risk":
                    update_fields.append(f'"riskScore" = ${param_num}')
                    update_values.append(result_data.score)
                    param_num += 1
                
                if update_fields:
                    update_fields.append(f'"updatedAt" = ${param_num}')
                    update_values.append(datetime.utcnow())
                    param_num += 1
                    update_values.append(result_data.sessionId)
                    
                    await conn.execute(f'''
                        UPDATE video_kyc_sessions 
                        SET {", ".join(update_fields)}
                        WHERE id = ${param_num}
                    ''', *update_values)
                
                return verification_result
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to add verification result: {str(e)}")
            raise

    async def run_ai_analysis(self, session_id: str) -> Dict[str, Any]:
        """Run AI analysis on Video KYC session"""
        
        try:
            session = await self.get_session(session_id)
            
            if not session:
                raise ValueError("Session not found")
            
            # Update status to AI Analysis
            await self.update_session_status(session_id, VideoKYCStatusEnum.AI_ANALYSIS)
            
            analysis_results = {
                "documentVerified": session.get("documentVerified", False),
                "faceMatched": session.get("faceMatched", False),
                "livenessChecked": session.get("livenessChecked", False),
                "forgeryScore": session.get("forgeryScore"),
                "faceMatchScore": session.get("faceMatchScore"),
                "deepfakeScore": session.get("deepfakeScore"),
                "riskScore": session.get("riskScore"),
            }
            
            # Calculate overall recommendation
            all_checks_passed = (
                session.get("documentVerified", False) and 
                session.get("faceMatched", False) and 
                session.get("livenessChecked", False)
            )
            
            risk_score = session.get("riskScore")
            risk_acceptable = risk_score is None or risk_score < 500
            
            if all_checks_passed and risk_acceptable:
                recommendation = "APPROVED"
            elif not all_checks_passed or (risk_score and risk_score > 700):
                recommendation = "REJECTED"
            else:
                recommendation = "MANUAL_REVIEW"
            
            analysis_results["recommendation"] = recommendation
            
            logger.info(f"[VIDEO-KYC] AI analysis completed for session {session_id}: {recommendation}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to run AI analysis: {str(e)}")
            raise

    async def complete_session(self, session_id: str, final_decision: VerificationDecisionEnum,
                              agent_name: Optional[str] = None, 
                              agent_review_notes: Optional[str] = None,
                              rejection_reason: Optional[str] = None) -> Dict[str, Any]:
        """Complete Video KYC session with final decision"""
        
        try:
            status = VideoKYCStatusEnum.COMPLETED if final_decision == VerificationDecisionEnum.APPROVED else VideoKYCStatusEnum.REJECTED
            
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow('''
                    UPDATE video_kyc_sessions 
                    SET "sessionStatus" = $1, "finalDecision" = $2, "sessionCompletedAt" = $3,
                        "agentName" = $4, "agentReviewNotes" = $5, "rejectionReason" = $6,
                        "updatedAt" = $7
                    WHERE id = $8
                    RETURNING *
                ''', status, final_decision, datetime.utcnow(), agent_name, agent_review_notes,
                rejection_reason, datetime.utcnow(), session_id)
                
                session = dict(result)
            
            logger.info(f"[VIDEO-KYC] Session {session_id} completed with decision: {final_decision}")
            return session
            
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to complete session: {str(e)}")
            raise

    async def get_user_sessions(self, user_id: str, limit: int = 10, 
                               skip: int = 0) -> List[Dict[str, Any]]:
        """Get user's Video KYC session history"""
        
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch('''
                    SELECT * FROM video_kyc_sessions 
                    WHERE "userId" = $1
                    ORDER BY "sessionStartedAt" DESC
                    LIMIT $2 OFFSET $3
                ''', user_id, limit, skip)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to get user sessions: {str(e)}")
            raise

    async def get_session_count(self, user_id: str) -> int:
        """Get count of user's Video KYC sessions"""
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('''
                    SELECT COUNT(*) FROM video_kyc_sessions WHERE "userId" = $1
                ''', user_id)
                
                return result
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to get session count: {str(e)}")
            raise

    async def save_id_document(self, session_id: str, id_number: str, 
                              full_text: str, ocr_json: Dict[str, Any], 
                              confidence: float) -> str:
        """
        Save OCR result from ID document to database
        
        Args:
            session_id: Video KYC session ID
            id_number: Extracted ID number
            full_text: Full text extracted from document
            ocr_json: Complete OCR result JSON
            confidence: Confidence score
            
        Returns:
            Document ID
        """
        try:
            async with self.pool.acquire() as conn:
                document_id = str(uuid.uuid4())
                
                await conn.execute('''
                    INSERT INTO video_kyc_documents 
                    (id, "sessionId", "idNumber", "fullText", "ocrJson", confidence, 
                     "isValid", "createdAt", "processedAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ''', document_id, session_id, id_number, full_text, ocr_json, 
                confidence, confidence >= 0.7, datetime.utcnow(), datetime.utcnow())
                
                logger.info(f"[VIDEO-KYC] ID document saved: {document_id}")
                return document_id
                
        except Exception as e:
            logger.error(f"[VIDEO-KYC] Failed to save ID document: {str(e)}")
            raise

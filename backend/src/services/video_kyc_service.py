"""
Video KYC Service - Business logic for Video KYC verification
"""

import os
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
from ..schemas.video_kyc import (
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


class VideoKYCService:
    """Service for Video KYC verification operations"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.upload_dir = "uploads/video_kyc"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def create_session(self, user_id: str, ip_address: Optional[str] = None, 
                            user_agent: Optional[str] = None):
        """Create a new Video KYC session"""
        
        async with self.pool.acquire() as conn:
            session_id = f"vkyc_{os.urandom(16).hex()}"
            
            await conn.execute('''
                INSERT INTO video_kyc_sessions 
                (id, "userId", "sessionStatus", "currentStep", "totalSteps", "ipAddress", "userAgent", 
                 "documentVerified", "faceMatched", "livenessChecked", "finalDecision")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ''', session_id, user_id, 'IDLE', 0, 8, ip_address, user_agent, False, False, False, 'PENDING')
            
            # Fetch the created session
            session = await conn.fetchrow('''
                SELECT * FROM video_kyc_sessions WHERE id = $1
            ''', session_id)
            
            return dict(session)

    async def get_session(self, session_id: str) -> Optional[VideoKYCSession]:
        """Get Video KYC session by ID"""
        
        session = await self.db.videokycession.find_unique(
            where={"id": session_id},
            include={
                "questions": True,
                "answers": True,
                "verificationResults": True,
                "chatMessages": {"order_by": {"timestamp": "asc"}},
            }
        )
        
        return session

    async def update_session(self, session_id: str, 
                           update_data: VideoKYCSessionUpdate) -> VideoKYCSession:
        """Update Video KYC session"""
        
        data_dict = update_data.dict(exclude_none=True)
        
        session = await self.db.videokycession.update(
            where={"id": session_id},
            data=data_dict
        )
        
        return session

    async def update_session_status(self, session_id: str, 
                                   status: VideoKYCStatusEnum) -> VideoKYCSession:
        """Update session status"""
        
        session = await self.db.videokycession.update(
            where={"id": session_id},
            data={"sessionStatus": status}
        )
        
        return session

    async def add_question(self, question_data: VideoKYCQuestionCreate):
        """Add a question to Video KYC session"""
        
        question = await self.db.videokyequestion.create(
            data={
                "sessionId": question_data.sessionId,
                "questionText": question_data.questionText,
                "questionType": question_data.questionType,
                "questionOrder": question_data.questionOrder,
                "validationRules": question_data.validationRules,
                "required": question_data.required,
            }
        )
        
        return question

    async def add_answer(self, answer_data: VideoKYCAnswerCreate):
        """Add an answer to a Video KYC question"""
        
        answer = await self.db.videokyanswer.create(
            data={
                "sessionId": answer_data.sessionId,
                "questionId": answer_data.questionId,
                "answerText": answer_data.answerText,
                "answerType": answer_data.answerType,
                "responseTime": answer_data.responseTime,
            }
        )
        
        # Update session with the answer data
        question = await self.db.videokyequestion.find_unique(
            where={"id": answer_data.questionId}
        )
        
        if question:
            field_map = {
                "name": "name",
                "dob": "dateOfBirth",
                "address": "address",
                "income": "income",
                "employment": "employment",
                "aadhar": "aadhar",
                "pan": "pan",
            }
            
            if question.questionType in field_map:
                await self.db.videokycession.update(
                    where={"id": answer_data.sessionId},
                    data={field_map[question.questionType]: answer_data.answerText}
                )
        
        return answer

    async def add_chat_message(self, message_data: VideoKYCChatMessageCreate):
        """Add a chat message to Video KYC session"""
        
        message = await self.db.videokycchatmessage.create(
            data={
                "sessionId": message_data.sessionId,
                "messageText": message_data.messageText,
                "messageType": message_data.messageType,
            }
        )
        
        return message

    async def save_uploaded_file(self, session_id: str, file_data: bytes, 
                                file_type: str, filename: str) -> str:
        """Save uploaded file and return file path"""
        
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
            await self.db.videokycession.update(
                where={"id": session_id},
                data={field_map[file_type]: file_path}
            )
        
        return file_path

    async def add_verification_result(self, result_data: VideoKYCVerificationResultCreate):
        """Add a verification result to Video KYC session"""
        
        result = await self.db.videokycverificationresult.create(
            data={
                "sessionId": result_data.sessionId,
                "verificationType": result_data.verificationType,
                "score": result_data.score,
                "confidence": result_data.confidence,
                "isPassed": result_data.isPassed,
                "details": result_data.details,
                "modelVersion": result_data.modelVersion,
                "processingTime": result_data.processingTime,
            }
        )
        
        # Update session with verification scores
        update_data = {}
        
        if result_data.verificationType == "document":
            update_data["documentVerified"] = result_data.isPassed
            update_data["forgeryScore"] = result_data.score
        elif result_data.verificationType == "face_match":
            update_data["faceMatched"] = result_data.isPassed
            update_data["faceMatchScore"] = result_data.score
        elif result_data.verificationType == "deepfake":
            update_data["livenessChecked"] = result_data.isPassed
            update_data["deepfakeScore"] = result_data.score
        elif result_data.verificationType == "risk":
            update_data["riskScore"] = result_data.score
        
        if update_data:
            await self.db.videokycession.update(
                where={"id": result_data.sessionId},
                data=update_data
            )
        
        return result

    async def run_ai_analysis(self, session_id: str) -> Dict[str, Any]:
        """Run AI analysis on Video KYC session"""
        
        session = await self.get_session(session_id)
        
        if not session:
            raise ValueError("Session not found")
        
        # Update status to AI Analysis
        await self.update_session_status(session_id, VideoKYCStatusEnum.AI_ANALYSIS)
        
        analysis_results = {
            "documentVerified": session.documentVerified,
            "faceMatched": session.faceMatched,
            "livenessChecked": session.livenessChecked,
            "forgeryScore": session.forgeryScore,
            "faceMatchScore": session.faceMatchScore,
            "deepfakeScore": session.deepfakeScore,
            "riskScore": session.riskScore,
        }
        
        # Calculate overall recommendation
        all_checks_passed = (
            session.documentVerified and 
            session.faceMatched and 
            session.livenessChecked
        )
        
        risk_acceptable = session.riskScore is None or session.riskScore < 500
        
        if all_checks_passed and risk_acceptable:
            recommendation = "APPROVED"
        elif not all_checks_passed or (session.riskScore and session.riskScore > 700):
            recommendation = "REJECTED"
        else:
            recommendation = "MANUAL_REVIEW"
        
        analysis_results["recommendation"] = recommendation
        
        return analysis_results

    async def complete_session(self, session_id: str, final_decision: VerificationDecisionEnum,
                              agent_name: Optional[str] = None, 
                              agent_review_notes: Optional[str] = None,
                              rejection_reason: Optional[str] = None) -> VideoKYCSession:
        """Complete Video KYC session with final decision"""
        
        session = await self.db.videokycession.update(
            where={"id": session_id},
            data={
                "sessionStatus": VideoKYCStatusEnum.COMPLETED if final_decision == VerificationDecisionEnum.APPROVED else VideoKYCStatusEnum.REJECTED,
                "finalDecision": final_decision,
                "sessionCompletedAt": datetime.now(),
                "agentName": agent_name,
                "agentReviewNotes": agent_review_notes,
                "rejectionReason": rejection_reason,
            }
        )
        
        return session

    async def get_user_sessions(self, user_id: str, limit: int = 10, 
                               skip: int = 0) -> List[VideoKYCSession]:
        """Get user's Video KYC session history"""
        
        sessions = await self.db.videokycession.find_many(
            where={"userId": user_id},
            order_by={"sessionStartedAt": "desc"},
            take=limit,
            skip=skip,
        )
        
        return sessions

    async def get_session_count(self, user_id: str) -> int:
        """Get count of user's Video KYC sessions"""
        
        count = await self.db.videokycession.count(
            where={"userId": user_id}
        )
        
        return count

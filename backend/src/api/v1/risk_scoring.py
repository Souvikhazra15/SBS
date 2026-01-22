"""
Risk Scoring API Routes

RESTful endpoints for intelligent risk assessment and decision engine.
Aggregates multiple verification results to calculate overall risk scores.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.schemas.feature import RiskScoringRequest, FeatureRunResponse
from src.schemas.session import VerificationSessionResponse, SessionStatsResponse
from src.services.risk_engine import RiskEngine, RiskLevel, DecisionRecommendation
from src.utils.auth import get_current_active_user, require_admin
from src.config.prisma import prisma

router = APIRouter(prefix="/risk-scoring", tags=["Risk Scoring"])
risk_engine = RiskEngine()

@router.post("/run", response_model=FeatureRunResponse)
async def run_risk_assessment(
    risk_request: RiskScoringRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Run comprehensive risk assessment for a verification session.
    
    - **session_id**: UUID of the verification session to assess
    - **additional_data**: Optional additional context data
    
    Returns detailed risk assessment including:
    - Overall risk score (0-1000)
    - Risk level classification
    - Decision recommendation
    - Component risk breakdown
    - Contributing risk factors
    """
    try:
        # Fetch verification session and related data
        session = await prisma.verificationsession.find_unique(
            where={"id": risk_request.session_id},
            include={
                "featureResults": True
            }
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification session not found"
            )
        
        # Ensure user owns this session
        if session.userId != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this verification session"
            )
        
        # Prepare session data for risk assessment
        session_data = {
            "forgeryScore": session.forgeryScore,
            "faceMatchScore": session.faceMatchScore,
            "deepfakeScore": session.deepfakeScore,
            "createdAt": session.createdAt.isoformat(),
            "featureResults": [
                {
                    "featureName": result.featureName,
                    "score": result.score,
                    "metadata": result.metadata
                }
                for result in session.featureResults
            ]
        }
        
        # Run risk assessment
        risk_assessment = risk_engine.calculate_risk_score(
            session_data,
            risk_request.additional_data
        )
        
        if "error" in risk_assessment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Risk assessment failed: {risk_assessment['error']}"
            )
        
        # Update verification session with risk score
        updated_session = await prisma.verificationsession.update(
            where={"id": session.id},
            data={
                "riskScore": risk_assessment["risk_score"],
                "decision": risk_assessment["recommendation"]
            }
        )
        
        # Store risk assessment result
        await prisma.featureresult.create({
            "sessionId": session.id,
            "featureName": "risk_scoring",
            "score": risk_assessment["risk_score"],
            "metadata": risk_assessment
        })
        
        return FeatureRunResponse(
            session_id=session.id,
            feature_name="risk_scoring",
            score=risk_assessment["risk_score"],
            metadata=risk_assessment,
            processing_time_ms=risk_assessment["processing_metadata"]["processing_time_ms"],
            status="completed",
            created_at=updated_session.updatedAt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{session_id}", response_model=FeatureRunResponse)
async def get_risk_assessment_result(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Retrieve risk assessment results for a specific session.
    
    - **session_id**: UUID of the verification session
    
    Returns stored risk assessment including overall score and detailed breakdown.
    """
    try:
        feature_result = await prisma.featureresult.find_first(
            where={
                "sessionId": session_id,
                "featureName": "risk_scoring",
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
                detail="Risk assessment result not found for this session"
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

@router.post("/batch-assess", response_model=List[Dict[str, Any]])
async def batch_risk_assessment(
    session_ids: List[str],
    additional_data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Run risk assessment on multiple sessions in batch.
    
    - **session_ids**: List of verification session UUIDs (max 50)
    - **additional_data**: Optional additional context data applied to all sessions
    
    Returns array of risk assessment results for each session.
    """
    try:
        # Limit batch size
        if len(session_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 sessions allowed in batch assessment"
            )
        
        results = []
        
        for session_id in session_ids:
            try:
                # Fetch session
                session = await prisma.verificationsession.find_unique(
                    where={"id": session_id},
                    include={"featureResults": True}
                )
                
                if not session or session.userId != current_user["id"]:
                    results.append({
                        "session_id": session_id,
                        "error": "Session not found or access denied",
                        "status": "failed"
                    })
                    continue
                
                # Prepare session data
                session_data = {
                    "forgeryScore": session.forgeryScore,
                    "faceMatchScore": session.faceMatchScore,
                    "deepfakeScore": session.deepfakeScore,
                    "createdAt": session.createdAt.isoformat()
                }
                
                # Run risk assessment
                risk_assessment = risk_engine.calculate_risk_score(
                    session_data,
                    additional_data
                )
                
                if "error" in risk_assessment:
                    results.append({
                        "session_id": session_id,
                        "error": risk_assessment["error"],
                        "status": "failed"
                    })
                    continue
                
                # Update session
                await prisma.verificationsession.update(
                    where={"id": session.id},
                    data={
                        "riskScore": risk_assessment["risk_score"],
                        "decision": risk_assessment["recommendation"]
                    }
                )
                
                # Store result
                await prisma.featureresult.create({
                    "sessionId": session.id,
                    "featureName": "risk_scoring",
                    "score": risk_assessment["risk_score"],
                    "metadata": risk_assessment
                })
                
                results.append({
                    "session_id": session_id,
                    "risk_score": risk_assessment["risk_score"],
                    "risk_level": risk_assessment["risk_level"],
                    "recommendation": risk_assessment["recommendation"],
                    "confidence": risk_assessment["confidence"],
                    "status": "completed"
                })
                
            except Exception as session_error:
                results.append({
                    "session_id": session_id,
                    "error": str(session_error),
                    "status": "failed"
                })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch assessment failed: {str(e)}"
        )

@router.get("/dashboard/stats", response_model=SessionStatsResponse)
async def get_risk_dashboard_stats(
    days: int = Query(30, description="Number of days for statistics"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get risk assessment statistics for user dashboard.
    
    - **days**: Number of days to include in statistics (default: 30)
    
    Returns comprehensive statistics about user's verification sessions.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's sessions in date range
        sessions = await prisma.verificationsession.find_many(
            where={
                "userId": current_user["id"],
                "createdAt": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        )
        
        # Calculate statistics
        total_sessions = len(sessions)
        completed_sessions = len([s for s in sessions if s.riskScore is not None])
        pending_sessions = total_sessions - completed_sessions
        
        approved_sessions = len([s for s in sessions if s.decision == "APPROVED"])
        rejected_sessions = len([s for s in sessions if s.decision == "REJECTED"])
        manual_review_sessions = len([s for s in sessions if s.decision == "MANUAL_REVIEW"])
        
        # Calculate average processing time (simulated)
        avg_processing_time = 4500 if completed_sessions > 0 else None  # 4.5 seconds average
        
        # Calculate success rate
        success_rate = (approved_sessions / completed_sessions * 100) if completed_sessions > 0 else None
        
        return SessionStatsResponse(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            pending_sessions=pending_sessions,
            approved_sessions=approved_sessions,
            rejected_sessions=rejected_sessions,
            manual_review_sessions=manual_review_sessions,
            average_processing_time=avg_processing_time,
            success_rate=success_rate
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )

@router.get("/admin/risk-distribution", dependencies=[Depends(require_admin)])
async def get_risk_distribution(
    days: int = Query(30, description="Number of days for analysis")
):
    """
    Get risk score distribution across all users (Admin only).
    
    - **days**: Number of days to include in analysis
    
    Returns risk level distribution and trends for administrative oversight.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all sessions with risk scores
        sessions = await prisma.verificationsession.find_many(
            where={
                "createdAt": {
                    "gte": start_date,
                    "lte": end_date
                },
                "riskScore": {
                    "not": None
                }
            }
        )
        
        # Calculate risk level distribution
        risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        
        for session in sessions:
            score = session.riskScore
            if score <= 250:
                risk_levels["LOW"] += 1
            elif score <= 500:
                risk_levels["MEDIUM"] += 1
            elif score <= 750:
                risk_levels["HIGH"] += 1
            else:
                risk_levels["CRITICAL"] += 1
        
        total_assessed = len(sessions)
        
        return {
            "period_days": days,
            "total_sessions_assessed": total_assessed,
            "risk_distribution": risk_levels,
            "risk_percentages": {
                level: round(count / total_assessed * 100, 2) if total_assessed > 0 else 0
                for level, count in risk_levels.items()
            },
            "average_risk_score": round(sum(s.riskScore for s in sessions) / total_assessed, 2) if total_assessed > 0 else 0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch risk distribution: {str(e)}"
        )

@router.get("/info")
async def get_service_info():
    """
    Get information about the risk scoring service.
    
    Returns model capabilities, thresholds, and scoring methodology.
    """
    return {
        "service_name": "Risk Scoring Engine",
        **risk_engine.get_model_info(),
        "capabilities": [
            "Comprehensive risk assessment",
            "Multi-factor analysis",
            "ML-based risk calculation",
            "Behavioral pattern detection",
            "Geolocation risk analysis",
            "Device fingerprinting",
            "Historical data integration"
        ],
        "assessment_factors": [
            "Document authenticity score",
            "Face matching confidence",
            "Deepfake detection results",
            "Behavioral anomalies",
            "Geolocation consistency",
            "Device reputation",
            "Session characteristics"
        ]
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    """
    return {
        "status": "healthy",
        "service": "risk_scoring",
        "timestamp": datetime.utcnow().isoformat(),
        "version": risk_engine.model_version
    }

"""API routes for Lead Health Score"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.core.db import get_db
from app.core.orm import LeadORM
from app.api.routes_workspaces import get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM
from app.services.health_score import HealthScoreCalculator

router = APIRouter()


@router.get("/leads/{lead_id}/health-score")
async def get_lead_health_score(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get health score for a specific lead"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    lead = db.query(LeadORM).filter(
        and_(
            LeadORM.id == lead_id,
            LeadORM.organization_id == current_workspace.organization_id,
        )
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get email verification status
    email_status = None
    if hasattr(lead, "email_records") and lead.email_records:
        for email_record in sorted(
            lead.email_records,
            key=lambda x: x.created_at if hasattr(x, "created_at") and x.created_at else datetime.min,
            reverse=True
        ):
            if hasattr(email_record, "verification_status"):
                email_status = email_record.verification_status
                break
    
    health_score = HealthScoreCalculator.calculate(lead, email_status)
    
    # Update lead's health_score field if it exists
    if hasattr(lead, "health_score"):
        lead.health_score = health_score["score"]
        if hasattr(lead, "health_score_last_calculated_at"):
            lead.health_score_last_calculated_at = datetime.now(timezone.utc)
        db.commit()
    
    return health_score


@router.post("/leads/health-score/calculate-batch")
async def calculate_health_scores_batch(
    lead_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Calculate health scores for multiple leads"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    query = db.query(LeadORM).filter(
        LeadORM.organization_id == current_workspace.organization_id
    )
    
    if lead_ids:
        query = query.filter(LeadORM.id.in_(lead_ids))
    
    leads = query.limit(1000).all()  # Limit to prevent timeout
    
    results = HealthScoreCalculator.calculate_batch(leads, db)
    
    # Update health scores in database
    for lead_id, health_data in results.items():
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if lead and hasattr(lead, "health_score"):
            lead.health_score = health_data["score"]
            if hasattr(lead, "health_score_last_calculated_at"):
                lead.health_score_last_calculated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "calculated": len(results),
        "scores": results,
    }


@router.get("/leads/health-score/stats")
async def get_health_score_stats(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get aggregate health score statistics"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    leads = db.query(LeadORM).filter(
        LeadORM.organization_id == current_workspace.organization_id
    ).all()
    
    if not leads:
        return {
            "total_leads": 0,
            "average_score": 0,
            "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "recommendations_summary": {},
        }
    
    # Calculate scores for all leads
    scores = HealthScoreCalculator.calculate_batch(leads, db)
    
    # Aggregate statistics
    total_score = sum(s["score"] for s in scores.values())
    average_score = total_score / len(scores) if scores else 0
    
    grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    recommendations_count = {}
    
    for health_data in scores.values():
        grade = health_data["grade"]
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        for rec in health_data["recommendations"]:
            recommendations_count[rec] = recommendations_count.get(rec, 0) + 1
    
    # Top recommendations
    top_recommendations = sorted(
        recommendations_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return {
        "total_leads": len(leads),
        "average_score": round(average_score, 1),
        "grade_distribution": grade_distribution,
        "top_recommendations": [{"action": k, "count": v} for k, v in top_recommendations],
    }


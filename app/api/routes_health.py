"""Health & Quality Dashboard API routes"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from pydantic import BaseModel
from datetime import datetime, date, timedelta

from app.core.db import get_db
from app.core.orm_health import WorkspaceDailyMetricsORM, WorkspaceHealthSnapshotORM
from app.core.orm_workspaces import WorkspaceORM
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace, get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.api.dependencies import require_super_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class HealthCard(BaseModel):
    status: str  # "ok", "warning", "bad"
    details: Dict[str, Any]


class HealthResponse(BaseModel):
    health_score: int
    period: str
    cards: Dict[str, HealthCard]
    charts: Dict[str, List[Dict[str, Any]]]


class WorkspaceHealthSummary(BaseModel):
    workspace_id: int
    name: str
    health_score: int
    bounce_rate: float
    jobs_failed_recent: int
    linkedin_failure_rate: float


# ============================================================================
# Helper Functions
# ============================================================================

def compute_health_score(metrics_window: Dict[str, Any]) -> int:
    """Compute health score (0-100) from metrics"""
    score = 100
    
    emails_sent = metrics_window.get("emails_sent", 0)
    emails_bounced = metrics_window.get("emails_bounced", 0)
    
    if emails_sent > 0:
        bounce_rate = emails_bounced / emails_sent
        if bounce_rate > 0.1:  # >10%
            score -= 25
        elif bounce_rate > 0.05:  # >5%
            score -= 10
    
    emails_verified = metrics_window.get("emails_verified", 0)
    ver_invalid = metrics_window.get("ver_invalid", 0)
    
    if emails_verified > 0:
        invalid_rate = ver_invalid / emails_verified
        if invalid_rate > 0.3:  # >30%
            score -= 15
    
    jobs_started = metrics_window.get("jobs_started", 0)
    jobs_failed = metrics_window.get("jobs_failed", 0)
    
    if jobs_started > 0:
        failure_rate = jobs_failed / jobs_started
        if failure_rate > 0.05:  # >5%
            score -= 10
    
    linkedin_success = metrics_window.get("linkedin_success", 0)
    linkedin_failed = metrics_window.get("linkedin_failed", 0)
    linkedin_total = linkedin_success + linkedin_failed
    
    if linkedin_total > 0:
        failure_rate = linkedin_failed / linkedin_total
        if failure_rate > 0.2:  # >20%
            score -= 10
    
    return max(0, min(100, score))


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=HealthResponse)
def get_workspace_health(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get health dashboard for current workspace"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Aggregate metrics for the period
    metrics = (
        db.query(
            func.sum(WorkspaceDailyMetricsORM.emails_sent).label("emails_sent"),
            func.sum(WorkspaceDailyMetricsORM.emails_bounced).label("emails_bounced"),
            func.sum(WorkspaceDailyMetricsORM.emails_spam_complaints).label("emails_spam_complaints"),
            func.sum(WorkspaceDailyMetricsORM.emails_verified).label("emails_verified"),
            func.sum(WorkspaceDailyMetricsORM.ver_valid).label("ver_valid"),
            func.sum(WorkspaceDailyMetricsORM.ver_invalid).label("ver_invalid"),
            func.sum(WorkspaceDailyMetricsORM.ver_risky).label("ver_risky"),
            func.sum(WorkspaceDailyMetricsORM.campaign_sends).label("campaign_sends"),
            func.sum(WorkspaceDailyMetricsORM.campaign_opens).label("campaign_opens"),
            func.sum(WorkspaceDailyMetricsORM.campaign_replies).label("campaign_replies"),
            func.sum(WorkspaceDailyMetricsORM.linkedin_success).label("linkedin_success"),
            func.sum(WorkspaceDailyMetricsORM.linkedin_failed).label("linkedin_failed"),
            func.sum(WorkspaceDailyMetricsORM.jobs_started).label("jobs_started"),
            func.sum(WorkspaceDailyMetricsORM.jobs_failed).label("jobs_failed"),
        )
        .filter(
            WorkspaceDailyMetricsORM.workspace_id == workspace.id,
            WorkspaceDailyMetricsORM.date >= start_date,
            WorkspaceDailyMetricsORM.date <= end_date,
        )
        .first()
    )
    
    metrics_dict = {
        "emails_sent": metrics.emails_sent or 0,
        "emails_bounced": metrics.emails_bounced or 0,
        "emails_spam_complaints": metrics.emails_spam_complaints or 0,
        "emails_verified": metrics.emails_verified or 0,
        "ver_valid": metrics.ver_valid or 0,
        "ver_invalid": metrics.ver_invalid or 0,
        "ver_risky": metrics.ver_risky or 0,
        "campaign_sends": metrics.campaign_sends or 0,
        "campaign_opens": metrics.campaign_opens or 0,
        "campaign_replies": metrics.campaign_replies or 0,
        "linkedin_success": metrics.linkedin_success or 0,
        "linkedin_failed": metrics.linkedin_failed or 0,
        "jobs_started": metrics.jobs_started or 0,
        "jobs_failed": metrics.jobs_failed or 0,
    }
    
    # Compute health score
    health_score = compute_health_score(metrics_dict)
    
    # Build cards
    emails_sent = metrics_dict["emails_sent"]
    bounce_rate = (metrics_dict["emails_bounced"] / emails_sent) if emails_sent > 0 else 0
    spam_rate = (metrics_dict["emails_spam_complaints"] / emails_sent) if emails_sent > 0 else 0
    
    deliverability_status = "ok"
    if bounce_rate > 0.1:
        deliverability_status = "bad"
    elif bounce_rate > 0.05:
        deliverability_status = "warning"
    
    emails_verified = metrics_dict["emails_verified"]
    valid_pct = (metrics_dict["ver_valid"] / emails_verified) if emails_verified > 0 else 0
    invalid_pct = (metrics_dict["ver_invalid"] / emails_verified) if emails_verified > 0 else 0
    
    verification_status = "ok"
    if invalid_pct > 0.3:
        verification_status = "warning"
    
    campaign_sends = metrics_dict["campaign_sends"]
    open_rate = (metrics_dict["campaign_opens"] / campaign_sends) if campaign_sends > 0 else 0
    reply_rate = (metrics_dict["campaign_replies"] / campaign_sends) if campaign_sends > 0 else 0
    
    jobs_started = metrics_dict["jobs_started"]
    jobs_failed = metrics_dict["jobs_failed"]
    jobs_failure_rate = (jobs_failed / jobs_started) if jobs_started > 0 else 0
    
    jobs_status = "ok"
    if jobs_failure_rate > 0.05:
        jobs_status = "warning"
    
    # Get daily metrics for charts
    daily_metrics = (
        db.query(WorkspaceDailyMetricsORM)
        .filter(
            WorkspaceDailyMetricsORM.workspace_id == workspace.id,
            WorkspaceDailyMetricsORM.date >= start_date,
            WorkspaceDailyMetricsORM.date <= end_date,
        )
        .order_by(WorkspaceDailyMetricsORM.date)
        .all()
    )
    
    bounce_rate_by_day = []
    verification_valid_pct_by_day = []
    reply_rate_by_day = []
    
    for dm in daily_metrics:
        date_str = dm.date.isoformat()
        
        # Bounce rate
        daily_bounce_rate = (dm.emails_bounced / dm.emails_sent) if dm.emails_sent > 0 else 0
        bounce_rate_by_day.append({"date": date_str, "value": round(daily_bounce_rate * 100, 2)})
        
        # Verification valid %
        daily_valid_pct = (dm.ver_valid / dm.emails_verified) if dm.emails_verified > 0 else 0
        verification_valid_pct_by_day.append({"date": date_str, "value": round(daily_valid_pct * 100, 2)})
        
        # Reply rate
        daily_reply_rate = (dm.campaign_replies / dm.campaign_sends) if dm.campaign_sends > 0 else 0
        reply_rate_by_day.append({"date": date_str, "value": round(daily_reply_rate * 100, 2)})
    
    return HealthResponse(
        health_score=health_score,
        period=f"last_{days}_days",
        cards={
            "deliverability": HealthCard(
                status=deliverability_status,
                details={
                    "emails_sent": emails_sent,
                    "bounce_rate": round(bounce_rate, 4),
                    "spam_complaint_rate": round(spam_rate, 4),
                }
            ),
            "verification": HealthCard(
                status=verification_status,
                details={
                    "emails_verified": emails_verified,
                    "valid_pct": round(valid_pct, 2),
                    "invalid_pct": round(invalid_pct, 2),
                }
            ),
            "campaigns": HealthCard(
                status="ok",
                details={
                    "avg_open_rate": round(open_rate, 2),
                    "avg_reply_rate": round(reply_rate, 2),
                }
            ),
            "jobs": HealthCard(
                status=jobs_status,
                details={
                    "jobs_started": jobs_started,
                    "jobs_failed": jobs_failed,
                }
            ),
        },
        charts={
            "bounce_rate_by_day": bounce_rate_by_day,
            "verification_valid_pct_by_day": verification_valid_pct_by_day,
            "reply_rate_by_day": reply_rate_by_day,
        },
    )


@router.get("/admin/workspaces")
@router.get("/admin/health/all-workspaces")  # Alias for frontend compatibility
def get_all_workspaces_health(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """Get health summary for all workspaces (super admin only)"""
    # Get all workspaces
    workspaces = db.query(WorkspaceORM).all()
    
    results = []
    end_date = date.today()
    start_date = end_date - timedelta(days=7)  # Last 7 days for summary
    
    for workspace in workspaces:
        # Get recent metrics
        metrics = (
            db.query(
                func.sum(WorkspaceDailyMetricsORM.emails_sent).label("emails_sent"),
                func.sum(WorkspaceDailyMetricsORM.emails_bounced).label("emails_bounced"),
                func.sum(WorkspaceDailyMetricsORM.linkedin_success).label("linkedin_success"),
                func.sum(WorkspaceDailyMetricsORM.linkedin_failed).label("linkedin_failed"),
                func.sum(WorkspaceDailyMetricsORM.jobs_failed).label("jobs_failed"),
            )
            .filter(
                WorkspaceDailyMetricsORM.workspace_id == workspace.id,
                WorkspaceDailyMetricsORM.date >= start_date,
            )
            .first()
        )
        
        emails_sent = metrics.emails_sent or 0
        bounce_rate = (metrics.emails_bounced / emails_sent) if emails_sent > 0 else 0
        
        linkedin_total = (metrics.linkedin_success or 0) + (metrics.linkedin_failed or 0)
        linkedin_failure_rate = (metrics.linkedin_failed / linkedin_total) if linkedin_total > 0 else 0
        
        metrics_dict = {
            "emails_sent": emails_sent,
            "emails_bounced": metrics.emails_bounced or 0,
            "linkedin_success": metrics.linkedin_success or 0,
            "linkedin_failed": metrics.linkedin_failed or 0,
            "jobs_started": 0,  # Would need to query separately
            "jobs_failed": metrics.jobs_failed or 0,
        }
        
        health_score = compute_health_score(metrics_dict)
        
        results.append(WorkspaceHealthSummary(
            workspace_id=workspace.id,
            name=workspace.name,
            health_score=health_score,
            bounce_rate=round(bounce_rate, 4),
            jobs_failed_recent=metrics.jobs_failed or 0,
            linkedin_failure_rate=round(linkedin_failure_rate, 4),
        ))
    
    return results


@router.get("/stats")
def get_health_stats(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get health statistics (alias for backward compatibility)"""
    # Return a simple stats response
    # This endpoint is used by the frontend but doesn't have a specific implementation yet
    # For now, return empty stats
    return {
        "total_leads": 0,
        "average_score": 0,
        "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        "recommendations_summary": {},
    }

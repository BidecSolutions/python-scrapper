"""Dashboard statistics API routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.core.db import get_db
from app.core.orm import (
    LeadORM, ScrapeJobORM, OrganizationORM,
    EmailVerificationJobORM, EmailORM, EmailVerificationJobStatus
)

router = APIRouter()


def get_or_create_default_org(db: Session) -> OrganizationORM:
    """Get or create default organization for testing"""
    org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
    
    if not org:
        org = OrganizationORM(
            name="Acme Growth Agency",
            slug="default",
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    
    return org


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    org = get_or_create_default_org(db)
    org_id = org.id
    
    # Total leads
    total_leads = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org_id
    ).scalar() or 0
    
    # Leads this month
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    leads_this_month = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org_id,
        LeadORM.created_at >= start_of_month
    ).scalar() or 0
    
    # Average lead score
    avg_score_result = db.query(func.avg(LeadORM.quality_score)).filter(
        LeadORM.organization_id == org_id,
        LeadORM.quality_score.isnot(None)
    ).scalar()
    avg_score = round(float(avg_score_result), 0) if avg_score_result else 0
    
    # AI Enriched percentage
    # Count leads with AI enrichment (has quality_score or metadata with ai_extracted)
    ai_enriched_count = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org_id,
        LeadORM.quality_score.isnot(None)
    ).scalar() or 0
    ai_enriched_pct = round((ai_enriched_count / total_leads * 100) if total_leads > 0 else 0, 0)
    
    # Calculate changes (compare this month to last month)
    last_month_start = (start_of_month - timedelta(days=32)).replace(day=1)
    last_month_end = start_of_month - timedelta(days=1)
    leads_last_month = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org_id,
        LeadORM.created_at >= last_month_start,
        LeadORM.created_at < start_of_month
    ).scalar() or 0
    
    # Calculate percentage changes
    month_change = 0
    if leads_last_month > 0:
        month_change = round(((leads_this_month - leads_last_month) / leads_last_month) * 100, 0)
    
    # Recent jobs (last 5)
    recent_jobs = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.organization_id == org_id
    ).order_by(ScrapeJobORM.created_at.desc()).limit(5).all()
    
    jobs_data = [
        {
            "id": job.id,
            "niche": job.niche,
            "location": job.location,
            "status": job.status.value,
            "result_count": job.result_count or 0,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        for job in recent_jobs
    ]
    
    return {
        "total_leads": total_leads,
        "leads_this_month": leads_this_month,
        "month_change": month_change,
        "avg_lead_score": int(avg_score),
        "ai_enriched_pct": int(ai_enriched_pct),
        "recent_jobs": jobs_data,
    }


@router.get("/dashboard/deliverability")
def get_deliverability_stats(
    db: Session = Depends(get_db),
):
    """
    Get email deliverability statistics
    
    Returns aggregated stats from verification jobs and email records
    """
    org = get_or_create_default_org(db)
    
    # Get all completed verification jobs
    completed_jobs = db.query(EmailVerificationJobORM).filter(
        EmailVerificationJobORM.organization_id == org.id,
        EmailVerificationJobORM.status == EmailVerificationJobStatus.completed
    ).all()
    
    # Aggregate stats from jobs
    total_verified = sum(job.total_emails for job in completed_jobs)
    total_valid = sum(job.valid_count for job in completed_jobs)
    total_invalid = sum(job.invalid_count for job in completed_jobs)
    total_risky = sum(job.risky_count for job in completed_jobs)
    total_unknown = sum(job.unknown_count for job in completed_jobs)
    total_disposable = sum(job.disposable_count for job in completed_jobs)
    total_syntax_error = sum(job.syntax_error_count for job in completed_jobs)
    
    # Get email records stats
    total_email_records = db.query(func.count(EmailORM.id)).filter(
        EmailORM.organization_id == org.id
    ).scalar() or 0
    
    verified_email_records = db.query(func.count(EmailORM.id)).filter(
        EmailORM.organization_id == org.id,
        EmailORM.verify_status.isnot(None)
    ).scalar() or 0
    
    valid_email_records = db.query(func.count(EmailORM.id)).filter(
        EmailORM.organization_id == org.id,
        EmailORM.verify_status == "valid"
    ).scalar() or 0
    
    invalid_email_records = db.query(func.count(EmailORM.id)).filter(
        EmailORM.organization_id == org.id,
        EmailORM.verify_status == "invalid"
    ).scalar() or 0
    
    risky_email_records = db.query(func.count(EmailORM.id)).filter(
        EmailORM.organization_id == org.id,
        EmailORM.verify_status == "risky"
    ).scalar() or 0
    
    # Calculate percentages
    valid_percent = (total_valid / total_verified * 100) if total_verified > 0 else 0
    invalid_percent = (total_invalid / total_verified * 100) if total_verified > 0 else 0
    risky_percent = (total_risky / total_verified * 100) if total_verified > 0 else 0
    unknown_percent = (total_unknown / total_verified * 100) if total_verified > 0 else 0
    
    # Verification rate (how many emails have been verified)
    verification_rate = (verified_email_records / total_email_records * 100) if total_email_records > 0 else 0
    
    return {
        "total_verified": total_verified,
        "total_email_records": total_email_records,
        "verified_email_records": verified_email_records,
        "verification_rate": round(verification_rate, 1),
        "breakdown": {
            "valid": {
                "count": total_valid,
                "percent": round(valid_percent, 1),
            },
            "invalid": {
                "count": total_invalid,
                "percent": round(invalid_percent, 1),
            },
            "risky": {
                "count": total_risky,
                "percent": round(risky_percent, 1),
            },
            "unknown": {
                "count": total_unknown,
                "percent": round(unknown_percent, 1),
            },
            "disposable": {
                "count": total_disposable,
                "percent": round((total_disposable / total_verified * 100) if total_verified > 0 else 0, 1),
            },
            "syntax_error": {
                "count": total_syntax_error,
                "percent": round((total_syntax_error / total_verified * 100) if total_verified > 0 else 0, 1),
            },
        },
        "email_records": {
            "total": total_email_records,
            "verified": verified_email_records,
            "valid": valid_email_records,
            "invalid": invalid_email_records,
            "risky": risky_email_records,
        },
        "recent_jobs": len(completed_jobs),
    }


@router.get("/dashboard/pipeline/summary")
def get_dashboard_pipeline_summary(
    db: Session = Depends(get_db),
):
    """Get pipeline summary for dashboard (alias for deals/pipeline/summary)"""
    # Try to import deals functionality
    try:
        from app.core.orm_deals import DealORM, DealStage
        from datetime import timedelta
        
        # Get all deals (simplified - in production should filter by workspace)
        org = get_or_create_default_org(db)
        
        # Query deals by organization (simplified approach)
        try:
            deals = db.query(DealORM).filter(DealORM.organization_id == org.id).all()
        except Exception:
            # If deals table doesn't exist or query fails, return empty summary
            deals = []
        
        # Calculate totals by stage
        stage_totals = {}
        stage_counts = {}
        for stage in DealStage:
            stage_deals = [d for d in deals if d.stage == stage]
            stage_counts[stage.value] = len(stage_deals)
            stage_totals[stage.value] = sum(float(d.value or 0) for d in stage_deals)
        
        # In-progress (all except won/lost)
        in_progress_deals = [d for d in deals if d.stage not in [DealStage.won, DealStage.lost]]
        in_progress_value = sum(float(d.value or 0) for d in in_progress_deals)
        
        # Won deals (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        won_recent = [d for d in deals if d.stage == DealStage.won and d.won_at and d.won_at >= thirty_days_ago]
        won_recent_value = sum(float(d.value or 0) for d in won_recent)
        
        # Win rate (last 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        closed_recent = [d for d in deals if (d.won_at or d.lost_at) and (d.won_at or d.lost_at) >= ninety_days_ago]
        won_recent_90 = [d for d in closed_recent if d.stage == DealStage.won]
        win_rate = (len(won_recent_90) / len(closed_recent) * 100) if closed_recent else 0
        
        # Average days to close (won deals)
        won_deals = [d for d in deals if d.stage == DealStage.won and d.won_at and d.created_at]
        avg_days_to_close = None
        if won_deals:
            days_list = [(d.won_at - d.created_at).days for d in won_deals if d.won_at and d.created_at]
            if days_list:
                avg_days_to_close = sum(days_list) / len(days_list)
        
        return {
            "stage_counts": stage_counts,
            "stage_totals": stage_totals,
            "in_progress_value": in_progress_value,
            "in_progress_count": len(in_progress_deals),
            "won_recent_value": won_recent_value,
            "won_recent_count": len(won_recent),
            "win_rate": round(win_rate, 1),
            "avg_days_to_close": round(avg_days_to_close, 1) if avg_days_to_close else None,
            "total_deals": len(deals),
        }
    except ImportError:
        # If deals module doesn't exist, return empty summary
        return {
            "stage_counts": {},
            "stage_totals": {},
            "in_progress_value": 0,
            "in_progress_count": 0,
            "won_recent_value": 0,
            "won_recent_count": 0,
            "win_rate": 0,
            "avg_days_to_close": None,
            "total_deals": 0,
        }
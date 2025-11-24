"""LinkedIn activity dashboard endpoints"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.core.db import get_db
from app.core.orm import OrganizationORM, LeadORM, EmailORM, EmailVerificationStatus
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


class VerificationStats(BaseModel):
    """Email verification statistics"""
    valid: int
    risky: int
    invalid: int
    unknown: int
    total: int


class LinkedInActivityResponse(BaseModel):
    """LinkedIn activity metrics"""
    leads_this_week: int
    total_leads: int
    verification_stats: VerificationStats
    verification_rate: float  # Percentage of valid emails


@router.get("/dashboard/linkedin", response_model=LinkedInActivityResponse)
def get_linkedin_activity(
    db: Session = Depends(get_db),
):
    """
    Get LinkedIn extension activity metrics
    
    Returns:
    - Leads captured this week
    - Total LinkedIn leads
    - Email verification breakdown
    - Verification rate
    """
    org = get_or_create_default_org(db)
    
    # Calculate start of week (Monday)
    now = datetime.utcnow()
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get LinkedIn leads this week
    leads_this_week = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "linkedin_extension",
        LeadORM.created_at >= start_of_week
    ).scalar() or 0
    
    # Get total LinkedIn leads
    total_leads = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "linkedin_extension"
    ).scalar() or 0
    
    # Get email verification stats for LinkedIn leads
    linkedin_lead_ids_subq = db.query(LeadORM.id).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "linkedin_extension"
    ).subquery()
    
    # Get all emails for LinkedIn leads
    linkedin_emails = db.query(EmailORM).filter(
        EmailORM.organization_id == org.id,
        EmailORM.lead_id.in_(db.query(linkedin_lead_ids_subq.c.id))
    ).all()
    
    # Build stats dict
    stats_dict = {
        "valid": 0,
        "risky": 0,
        "invalid": 0,
        "unknown": 0,
        "total": len(linkedin_emails)
    }
    
    for email in linkedin_emails:
        if email.verify_status:
            status_str = email.verify_status.value if hasattr(email.verify_status, 'value') else str(email.verify_status)
            if status_str in stats_dict:
                stats_dict[status_str] += 1
    
    # Calculate verification rate (valid / total)
    verification_rate = 0.0
    if stats_dict["total"] > 0:
        verification_rate = (stats_dict["valid"] / stats_dict["total"]) * 100
    
    return LinkedInActivityResponse(
        leads_this_week=leads_this_week,
        total_leads=total_leads,
        verification_stats=VerificationStats(**stats_dict),
        verification_rate=round(verification_rate, 1)
    )


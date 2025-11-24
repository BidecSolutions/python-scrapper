"""Email status API for leads"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.db import get_db
from app.core.orm import OrganizationORM, LeadORM, EmailORM
from app.schemas.linkedin import LeadEmailStatus
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/leads/{lead_id}/email-status", response_model=Optional[LeadEmailStatus])
def get_lead_email_status(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """
    Get current email status for a lead
    
    Returns email verification status if available, null otherwise
    """
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get most recent email record
    email_record = db.query(EmailORM).filter(
        EmailORM.organization_id == org.id,
        EmailORM.lead_id == lead.id
    ).order_by(EmailORM.created_at.desc()).first()
    
    if not email_record:
        return None
    
    return LeadEmailStatus(
        email=email_record.email,
        status=email_record.verify_status.value if email_record.verify_status else None,
        reason=email_record.verify_reason,
        confidence=float(email_record.verify_confidence) if email_record.verify_confidence else None,
        last_verified_at=email_record.verified_at,
    )


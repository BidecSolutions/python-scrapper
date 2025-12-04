"""Email tools API - First-class email finder and verifier endpoints"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.orm import (
    OrganizationORM, LeadORM, EmailORM, EmailVerificationJobORM,
    EmailVerificationItemORM, EmailVerificationJobStatus,
    EmailFinderJobORM, EmailFinderJobStatus,
)
from app.services.email_verifier import verify_email, VerificationStatus
from app.services.email_finder import find_email as find_email_service
from app.services.credit_manager import CreditManager
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class SingleVerifyRequest(BaseModel):
    """Request to verify a single email (lead-level)"""
    email: EmailStr
    lead_id: Optional[int] = None


class SingleVerifyResponse(BaseModel):
    """Response from single email verification"""
    email: str
    status: str
    reason: str
    confidence: Optional[float] = None
    email_id: Optional[int] = None


class BulkVerifyFromLeadsRequest(BaseModel):
    """Request to create bulk verification job from selected leads"""
    lead_ids: List[int] = Field(..., min_items=1)


class BulkVerifyFromCSVRequest(BaseModel):
    """Request to create bulk verification job from CSV"""
    emails: List[str] = Field(..., min_items=1)
    name: Optional[str] = None


class EmailFinderRequest(BaseModel):
    """Request to find email for a lead"""
    lead_id: int
    first_name: str
    last_name: str
    domain: str
    skip_smtp: bool = False
    min_confidence: float = Field(0.3, ge=0.0, le=1.0)


class EmailFinderResponse(BaseModel):
    """Response from email finder"""
    email: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    confidence: Optional[float] = None
    email_id: Optional[int] = None


# ============================================================================
# Single Email Verification (Lead-level)
# ============================================================================

@router.post("/email/verify", response_model=SingleVerifyResponse)
def verify_single_email(
    req: SingleVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify a single email address (lead-level)
    
    If lead_id is provided, updates or creates email record in emails table.
    """
    org = get_or_create_default_org(db)
    
    # Check credits
    if not CreditManager.check_balance(db, org.id, CreditManager.COST_EMAIL_VERIFIER):
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please upgrade your plan."
        )
    
    # Verify email
    status, reason = verify_email(req.email.lower())
    
    # Calculate confidence based on status
    confidence = None
    if status == VerificationStatus.VALID:
        confidence = 0.95
    elif status == VerificationStatus.RISKY:
        confidence = 0.7
    elif status == VerificationStatus.UNKNOWN:
        confidence = 0.4
    elif status in (VerificationStatus.DISPOSABLE, VerificationStatus.GIBBERISH):
        confidence = 0.1
    else:
        confidence = 0.0
    
    email_obj = None
    
    # If lead_id provided, create/update email record
    if req.lead_id:
        # Check if lead exists
        lead = db.query(LeadORM).filter(
            LeadORM.id == req.lead_id,
            LeadORM.organization_id == org.id
        ).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Find or create email record
        email_obj = db.query(EmailORM).filter(
            EmailORM.organization_id == org.id,
            EmailORM.lead_id == req.lead_id,
            EmailORM.email == req.email.lower()
        ).first()
        
        if not email_obj:
            email_obj = EmailORM(
                organization_id=org.id,
                lead_id=req.lead_id,
                email=req.email.lower(),
                label="primary",
                found_via="manual",
            )
            db.add(email_obj)
        
        # Update verification status
        email_obj.verify_status = status.value if hasattr(status, 'value') else str(status)
        email_obj.verify_reason = reason
        email_obj.verify_confidence = confidence
        email_obj.verified_at = datetime.utcnow()
        db.commit()
        db.refresh(email_obj)
    
    # Deduct credit
    CreditManager.deduct_credits(
        db, org.id, CreditManager.COST_EMAIL_VERIFIER,
        feature="email_verifier",
        description=f"Single email verification: {req.email}"
    )
    
    return SingleVerifyResponse(
        email=req.email.lower(),
        status=status.value if hasattr(status, 'value') else str(status),
        reason=reason,
        confidence=confidence,
        email_id=email_obj.id if email_obj else None,
    )


# ============================================================================
# Bulk Verification Jobs
# ============================================================================

@router.post("/email/verify/bulk-from-leads")
@router.post("/verification/jobs/from-leads")  # Alias for frontend compatibility
def create_bulk_verify_job_from_leads(
    req: BulkVerifyFromLeadsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create bulk verification job from selected leads
    
    Gathers primary emails from selected leads and creates a verification job.
    """
    org = get_or_create_default_org(db)
    
    if not req.lead_ids:
        raise HTTPException(status_code=400, detail="No leads provided")
    
    # Get leads
    leads = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.id.in_(req.lead_ids)
    ).all()
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found")
    
    # Create job
    job = EmailVerificationJobORM(
        organization_id=org.id,
        source_type="leads",
        source_description=f"Selected {len(leads)} leads",
        status=EmailVerificationJobStatus.pending,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Gather emails from leads
    items_to_create = []
    email_ids_seen = set()
    
    for lead in leads:
        # Get emails from emails table (canonical records)
        email_records = db.query(EmailORM).filter(
            EmailORM.organization_id == org.id,
            EmailORM.lead_id == lead.id
        ).all()
        
        # Also check legacy emails field
        legacy_emails = lead.emails or []
        
        # Process canonical email records
        for email_record in email_records:
            if email_record.id not in email_ids_seen:
                items_to_create.append(
                    EmailVerificationItemORM(
                        organization_id=org.id,
                        job_id=job.id,
                        email_id=email_record.id,
                        raw_email=email_record.email,
                        status="pending",
                    )
                )
                email_ids_seen.add(email_record.id)
        
        # Process legacy emails (create email records if needed)
        for email_str in legacy_emails:
            if not email_str:
                continue
            
            email_str = email_str.lower().strip()
            
            # Check if email record exists
            email_record = db.query(EmailORM).filter(
                EmailORM.organization_id == org.id,
                EmailORM.lead_id == lead.id,
                EmailORM.email == email_str
            ).first()
            
            if not email_record:
                # Create email record
                email_record = EmailORM(
                    organization_id=org.id,
                    lead_id=lead.id,
                    email=email_str,
                    label="primary",
                    found_via="scrape",
                )
                db.add(email_record)
                db.commit()
                db.refresh(email_record)
            
            if email_record.id not in email_ids_seen:
                items_to_create.append(
                    EmailVerificationItemORM(
                        organization_id=org.id,
                        job_id=job.id,
                        email_id=email_record.id,
                        raw_email=email_record.email,
                        status="pending",
                    )
                )
                email_ids_seen.add(email_record.id)
    
    # Bulk insert items
    if items_to_create:
        db.bulk_save_objects(items_to_create)
        job.total_emails = len(items_to_create)
    else:
        job.total_emails = 0
        job.status = EmailVerificationJobStatus.completed
        job.error_message = "No emails found in selected leads"
    
    db.commit()
    db.refresh(job)
    
    # Start background job (simplified - in production use Celery/RQ)
    if job.total_emails > 0:
        background_tasks.add_task(process_verification_job, job.id, org.id)
    
    return {
        "job_id": job.id,
        "status": job.status.value,
        "total_emails": job.total_emails,
    }


@router.post("/email/verify/bulk-from-csv")
@router.post("/verification/jobs/from-csv")  # Alias for frontend compatibility
def create_bulk_verify_job_from_csv(
    req: BulkVerifyFromCSVRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create bulk verification job from CSV email list
    """
    org = get_or_create_default_org(db)
    
    if not req.emails:
        raise HTTPException(status_code=400, detail="No emails provided")
    
    if len(req.emails) > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10,000 emails per job")
    
    # Create job
    job = EmailVerificationJobORM(
        organization_id=org.id,
        source_type="csv",
        source_description=req.name or f"CSV upload ({len(req.emails)} emails)",
        status=EmailVerificationJobStatus.pending,
        total_emails=len(req.emails),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Create items
    items_to_create = []
    for email_str in req.emails:
        if not email_str or not email_str.strip():
            continue
        
        email_str = email_str.strip().lower()
        
        items_to_create.append(
            EmailVerificationItemORM(
                organization_id=org.id,
                job_id=job.id,
                raw_email=email_str,
                status="pending",
            )
        )
    
    if items_to_create:
        db.bulk_save_objects(items_to_create)
        job.total_emails = len(items_to_create)
    else:
        job.total_emails = 0
        job.status = EmailVerificationJobStatus.completed
        job.error_message = "No valid emails provided"
    
    db.commit()
    db.refresh(job)
    
    # Start background job
    if job.total_emails > 0:
        background_tasks.add_task(process_verification_job, job.id, org.id)
    
    return {
        "job_id": job.id,
        "status": job.status.value,
        "total_emails": job.total_emails,
    }


# ============================================================================
# Single Email Finder (Lead-level)
# ============================================================================

@router.post("/email/finder", response_model=EmailFinderResponse)
def find_email_for_lead(
    req: EmailFinderRequest,
    db: Session = Depends(get_db),
):
    """
    Find email for a lead using pattern generation and verification
    """
    org = get_or_create_default_org(db)
    
    # Check credits
    if not CreditManager.check_balance(db, org.id, CreditManager.COST_EMAIL_FINDER):
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please upgrade your plan."
        )
    
    # Check if lead exists
    lead = db.query(LeadORM).filter(
        LeadORM.id == req.lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Find email
    result = find_email_service(
        req.first_name,
        req.last_name,
        req.domain,
        skip_smtp=req.skip_smtp,
        min_confidence=req.min_confidence
    )
    
    if not result:
        # Deduct credit even if not found (we tried)
        CreditManager.deduct_credits(
            db, org.id, CreditManager.COST_EMAIL_FINDER,
            feature="email_finder",
            description=f"Email finder (not found): {req.first_name} {req.last_name} @ {req.domain}"
        )
        raise HTTPException(status_code=404, detail="No confident email candidate found")
    
    # Extract result data (handle both EmailCandidateResult and dict)
    if hasattr(result, 'email'):
        email_str = result.email
        status_obj = result.status
        reason_str = result.reason
        confidence_val = result.score
    else:
        # Fallback for dict-like result
        email_str = result.get('email')
        status_obj = result.get('status')
        reason_str = result.get('reason', '')
        confidence_val = result.get('confidence') or result.get('score', 0.0)
    
    status_str = status_obj.value if hasattr(status_obj, 'value') else str(status_obj)
    
    # Create email record
    email_obj = EmailORM(
        organization_id=org.id,
        lead_id=req.lead_id,
        email=email_str,
        label="primary",
        verify_status=status_str,
        verify_reason=reason_str,
        verify_confidence=confidence_val,
        verified_at=datetime.utcnow(),
        found_via="finder",
    )
    db.add(email_obj)
    db.commit()
    db.refresh(email_obj)
    
    # Deduct credit
    CreditManager.deduct_credits(
        db, org.id, CreditManager.COST_EMAIL_FINDER,
        feature="email_finder",
        reference_id=email_obj.id,
        reference_type="email",
        description=f"Email finder: {email_str}"
    )
    
    return EmailFinderResponse(
        email=email_str,
        status=status_str,
        reason=reason_str,
        confidence=confidence_val,
        email_id=email_obj.id,
    )


# ============================================================================
# Job Management Endpoints
# ============================================================================

def _list_verification_jobs_impl(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
):
    """Internal implementation for listing verification jobs"""
    org = get_or_create_default_org(db)
    
    query = db.query(EmailVerificationJobORM).filter(
        EmailVerificationJobORM.organization_id == org.id
    )
    
    # Filter by status if provided
    if status:
        from app.core.orm import EmailVerificationJobStatus
        # Try to match status (case-insensitive)
        status_lower = status.lower()
        for enum_status in EmailVerificationJobStatus:
            if enum_status.value.lower() == status_lower:
                query = query.filter(EmailVerificationJobORM.status == enum_status)
                break
    
    jobs = query.order_by(EmailVerificationJobORM.created_at.desc()).limit(limit).offset(offset).all()
    
    return [
        {
            "id": job.id,
            "source_type": job.source_type,
            "source_description": job.source_description,
            "status": job.status.value,
            "total_emails": job.total_emails,
            "processed_count": job.processed_count,
            "valid_count": job.valid_count,
            "invalid_count": job.invalid_count,
            "risky_count": job.risky_count,
            "unknown_count": job.unknown_count,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
        for job in jobs
    ]


@router.get("/email/verification-jobs")
def list_verification_jobs(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
):
    """List all verification jobs for organization"""
    return _list_verification_jobs_impl(db, limit, offset, status)


@router.get("/verification/jobs")
def list_verification_jobs_alias(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
):
    """List all verification jobs (alias for frontend compatibility)"""
    return _list_verification_jobs_impl(db, limit, offset, status)


def _get_verification_job_impl(
    job_id: int,
    db: Session,
):
    """Internal implementation for getting verification job details"""
    org = get_or_create_default_org(db)
    
    job = db.query(EmailVerificationJobORM).filter(
        EmailVerificationJobORM.id == job_id,
        EmailVerificationJobORM.organization_id == org.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "source_type": job.source_type,
        "source_description": job.source_description,
        "status": job.status.value,
        "total_emails": job.total_emails,
        "processed_count": job.processed_count,
        "valid_count": job.valid_count,
        "invalid_count": job.invalid_count,
        "risky_count": job.risky_count,
        "unknown_count": job.unknown_count,
        "disposable_count": job.disposable_count,
        "syntax_error_count": job.syntax_error_count,
        "error_message": job.error_message,
        "credits_used": job.credits_used,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/email/verification-jobs/{job_id}")
def get_verification_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get verification job details"""
    return _get_verification_job_impl(job_id, db)


@router.get("/verification/jobs/{job_id}")
def get_verification_job_alias(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get verification job details (alias for frontend compatibility)"""
    return _get_verification_job_impl(job_id, db)


def _get_verification_job_results_impl(
    job_id: int,
    db: Session,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
):
    """Internal implementation for getting verification job results"""
    org = get_or_create_default_org(db)
    
    # Verify job exists and belongs to org
    job = db.query(EmailVerificationJobORM).filter(
        EmailVerificationJobORM.id == job_id,
        EmailVerificationJobORM.organization_id == org.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get verification items
    query = db.query(EmailVerificationItemORM).filter(
        EmailVerificationItemORM.job_id == job_id,
        EmailVerificationItemORM.organization_id == org.id
    )
    
    # Filter by status if provided
    if status:
        query = query.filter(EmailVerificationItemORM.verify_status == status)
    
    total = query.count()
    items = query.order_by(EmailVerificationItemORM.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "email": item.raw_email,
                "status": item.verify_status,
                "reason": item.verify_reason,
                "confidence": float(item.verify_confidence) if item.verify_confidence else None,
                "error": item.error,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


@router.get("/email/verification-jobs/{job_id}/results")
def get_verification_job_results(
    job_id: int,
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
):
    """Get verification job results (individual email items)"""
    return _get_verification_job_results_impl(job_id, db, limit, offset, status)


@router.get("/verification/jobs/{job_id}/results")
def get_verification_job_results_alias(
    job_id: int,
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
):
    """Get verification job results (alias for frontend compatibility)"""
    return _get_verification_job_results_impl(job_id, db, limit, offset, status)


# ============================================================================
# Background Job Processor
# ============================================================================

def process_verification_job(job_id: int, org_id: int):
    """
    Process email verification job in background
    
    This is a simplified version. In production, use Celery/RQ.
    """
    from app.core.db import SessionLocal
    from datetime import datetime
    
    db = SessionLocal()
    
    try:
        job = db.query(EmailVerificationJobORM).filter(
            EmailVerificationJobORM.id == job_id,
            EmailVerificationJobORM.organization_id == org_id
        ).first()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        job.status = EmailVerificationJobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Get pending items
        items = db.query(EmailVerificationItemORM).filter(
            EmailVerificationItemORM.job_id == job_id,
            EmailVerificationItemORM.organization_id == org_id,
            EmailVerificationItemORM.status == "pending"
        ).all()
        
        total_credits = 0
        
        for item in items:
            try:
                item.status = "processing"
                db.commit()
                
                # Verify email
                status, reason = verify_email(item.raw_email)
                status_str = status.value if hasattr(status, 'value') else str(status)
                
                # Calculate confidence based on status
                confidence = None
                if status == VerificationStatus.VALID:
                    confidence = 0.95
                elif status == VerificationStatus.RISKY:
                    confidence = 0.7
                elif status == VerificationStatus.UNKNOWN:
                    confidence = 0.4
                elif status in (VerificationStatus.DISPOSABLE, VerificationStatus.GIBBERISH):
                    confidence = 0.1
                else:
                    confidence = 0.0
                
                item.verify_status = status_str
                item.verify_reason = reason
                item.verify_confidence = confidence
                item.status = "done"
                
                # Update email record if linked
                if item.email_id:
                    email_obj = db.query(EmailORM).filter(EmailORM.id == item.email_id).first()
                    if email_obj:
                        email_obj.verify_status = status_str
                        email_obj.verify_reason = reason
                        email_obj.verify_confidence = confidence
                        email_obj.verified_at = datetime.utcnow()
                
                # Update job stats
                if status_str == "valid":
                    job.valid_count += 1
                elif status_str == "invalid":
                    job.invalid_count += 1
                elif status_str == "risky":
                    job.risky_count += 1
                elif status_str == "unknown":
                    job.unknown_count += 1
                elif status_str == "disposable":
                    job.disposable_count += 1
                elif status_str == "syntax_error":
                    job.syntax_error_count += 1
                
                job.processed_count += 1
                total_credits += CreditManager.COST_EMAIL_VERIFIER
                db.commit()
                
            except Exception as e:
                logger.error(f"Error processing item {item.id}: {e}", exc_info=True)
                item.status = "error"
                item.error = str(e)
                job.processed_count += 1
                db.commit()
        
        # Deduct credits
        if total_credits > 0:
            CreditManager.deduct_credits(
                db, org_id, total_credits,
                feature="email_verifier",
                reference_id=job_id,
                reference_type="email_verification_job",
                description=f"Bulk verification job: {job.total_emails} emails"
            )
            job.credits_used = total_credits
        
        job.status = EmailVerificationJobStatus.completed
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Verification job {job_id} completed: {job.processed_count}/{job.total_emails}")
        
    except Exception as e:
        logger.error(f"Error processing verification job {job_id}: {e}", exc_info=True)
        if job:
            job.status = EmailVerificationJobStatus.failed
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


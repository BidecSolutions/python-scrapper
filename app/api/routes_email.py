"""Email finder and verifier API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.core.orm import (
    OrganizationORM, PlanTier, EmailVerificationORM, EmailVerificationStatus,
    LeadORM, LeadStatus
)
from app.services.email_verifier import verify_email, VerificationStatus
from app.services.email_finder import find_email, EmailCandidateResult

logger = logging.getLogger(__name__)
router = APIRouter()


def get_or_create_default_org(db: Session) -> OrganizationORM:
    """Get or create default organization for testing"""
    org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
    
    if not org:
        org = OrganizationORM(
            name="Default Organization",
            slug="default",
            plan_tier=PlanTier.pro,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    
    return org


# ============================================================================
# Request/Response Models
# ============================================================================

class VerifyEmailRequest(BaseModel):
    """Request to verify an email"""
    email: EmailStr
    skip_smtp: bool = Field(False, description="Skip SMTP check (faster but less accurate)")


class VerifyEmailResponse(BaseModel):
    """Response from email verification"""
    email: str
    status: str
    reason: str
    confidence: Optional[float] = None
    cached: bool = False


class FindEmailRequest(BaseModel):
    """Request to find an email"""
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")
    domain: str = Field(..., min_length=3, description="Company domain (e.g., example.com)")
    skip_smtp: bool = Field(False, description="Skip SMTP check (faster but less accurate)")
    min_confidence: float = Field(0.3, ge=0.0, le=1.0, description="Minimum confidence score to return")


class FindEmailResponse(BaseModel):
    """Response from email finder"""
    email: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    confidence: Optional[float] = None
    candidates_checked: int = 0
    lead_id: Optional[int] = None  # If saved to leads


class SaveToLeadsRequest(BaseModel):
    """Request to save found email to leads"""
    first_name: str
    last_name: str
    email: str
    domain: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    confidence: Optional[float] = None
    job_id: Optional[int] = None  # Optional: link to existing job


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/email-verifier", response_model=VerifyEmailResponse)
def verify_email_endpoint(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Verify an email address
    
    Checks:
    - Syntax validation
    - Disposable domain detection
    - Gibberish detection
    - DNS MX records
    - SMTP acceptance (optional)
    """
    org = get_or_create_default_org(db)
    email = payload.email.lower().strip()
    
    # Check cache first
    cached = db.query(EmailVerificationORM).filter(
        EmailVerificationORM.organization_id == org.id,
        EmailVerificationORM.email == email
    ).first()
    
    if cached and not payload.skip_smtp:
        # Return cached result if available and SMTP wasn't skipped
        return VerifyEmailResponse(
            email=cached.email,
            status=cached.status.value,
            reason=cached.reason or "",
            confidence=float(cached.confidence) if cached.confidence else None,
            cached=True,
        )
    
    # Verify email
    status, reason = verify_email(email, skip_smtp=payload.skip_smtp)
    
    # Calculate confidence
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
    
    # Save to cache
    if cached:
        cached.status = EmailVerificationStatus(status.value)
        cached.reason = reason
        cached.confidence = confidence
        cached.smtp_checked = not payload.skip_smtp
        db.commit()
    else:
        verification = EmailVerificationORM(
            organization_id=org.id,
            email=email,
            status=EmailVerificationStatus(status.value),
            reason=reason,
            confidence=confidence,
            smtp_checked=not payload.skip_smtp,
        )
        db.add(verification)
        db.commit()
    
    return VerifyEmailResponse(
        email=email,
        status=status.value,
        reason=reason,
        confidence=confidence,
        cached=False,
    )


@router.post("/email-finder", response_model=FindEmailResponse)
def find_email_endpoint(
    payload: FindEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Find email address for a person
    
    Generates common email patterns and verifies them to find the most likely email.
    Uses learned patterns from existing leads if available.
    """
    org = get_or_create_default_org(db)
    
    # Normalize domain
    domain = payload.domain.lower().strip().lstrip("@")
    
    # Try to use learned patterns first
    try:
        from app.services.email_pattern_learner import enhance_email_finder_with_learning
        enhanced_candidates = enhance_email_finder_with_learning(
            db, org.id, domain, payload.first_name, payload.last_name
        )
        
        # Use enhanced finder if we have learned patterns
        if enhanced_candidates and len(enhanced_candidates) > 0:
            # Re-implement find_email with custom candidates
            from app.services.email_finder import score_candidate, EmailCandidateResult
            from app.services.email_verifier import verify_email, VerificationStatus
            
            best = None
            for email in enhanced_candidates:
                try:
                    status, reason = verify_email(email, skip_smtp=payload.skip_smtp)
                    score = score_candidate(status, reason)
                    
                    candidate_result = EmailCandidateResult(
                        email=email,
                        status=status,
                        reason=reason,
                        score=score,
                    )
                    
                    if best is None or candidate_result.score > best.score:
                        best = candidate_result
                    
                    if status == VerificationStatus.VALID and score >= 0.9:
                        break
                except Exception:
                    continue
            
            if best and best.score >= payload.min_confidence:
                result = best
            else:
                result = None
        else:
            # Fall back to default finder
            result = find_email(
                first_name=payload.first_name,
                last_name=payload.last_name,
                domain=domain,
                skip_smtp=payload.skip_smtp,
                min_confidence=payload.min_confidence,
            )
    except Exception as e:
        logger.warning(f"Error using learned patterns, falling back to default: {e}")
        # Fall back to default finder
        result = find_email(
            first_name=payload.first_name,
            last_name=payload.last_name,
            domain=domain,
            skip_smtp=payload.skip_smtp,
            min_confidence=payload.min_confidence,
        )
    
    if result is None:
        return FindEmailResponse(
            email=None,
            status=None,
            reason="no_confident_candidate",
            confidence=None,
            candidates_checked=0,
        )
    
    # Save verification to cache
    cached = db.query(EmailVerificationORM).filter(
        EmailVerificationORM.organization_id == org.id,
        EmailVerificationORM.email == result.email
    ).first()
    
    if not cached:
        verification = EmailVerificationORM(
            organization_id=org.id,
            email=result.email,
            status=EmailVerificationStatus(result.status.value),
            reason=result.reason,
            confidence=result.score,
            smtp_checked=not payload.skip_smtp,
        )
        db.add(verification)
        db.commit()
    
    return FindEmailResponse(
        email=result.email,
        status=result.status.value,
        reason=result.reason,
        confidence=result.score,
        candidates_checked=10,  # Approximate number of patterns checked
    )


@router.get("/email-verifier/bulk")
def verify_emails_bulk(
    emails: str = Query(..., description="Comma-separated list of emails"),
    skip_smtp: bool = Query(False, description="Skip SMTP check"),
    db: Session = Depends(get_db),
):
    """
    Verify multiple emails at once
    
    Returns list of verification results
    """
    email_list = [e.strip().lower() for e in emails.split(",") if e.strip()]
    
    if not email_list:
        raise HTTPException(status_code=400, detail="No valid emails provided")
    
    if len(email_list) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 emails per request")
    
    results = []
    for email in email_list:
        try:
            status, reason = verify_email(email, skip_smtp=skip_smtp)
            
            # Calculate confidence
            confidence = None
            if status == VerificationStatus.VALID:
                confidence = 0.95
            elif status == VerificationStatus.RISKY:
                confidence = 0.7
            elif status == VerificationStatus.UNKNOWN:
                confidence = 0.4
            else:
                confidence = 0.0
            
            results.append({
                "email": email,
                "status": status.value,
                "reason": reason,
                "confidence": confidence,
            })
        except Exception as e:
            results.append({
                "email": email,
                "status": "error",
                "reason": str(e),
                "confidence": None,
            })
    
    return {"results": results, "total": len(results)}


@router.post("/email-finder/save-to-leads")
def save_email_to_leads(
    payload: SaveToLeadsRequest,
    db: Session = Depends(get_db),
):
    """
    Save found email directly to leads
    
    Creates a new lead with the found email and verification status
    """
    org = get_or_create_default_org(db)
    
    # Check if lead already exists (by email or website)
    existing_lead = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.emails.contains([payload.email])
    ).first()
    
    if existing_lead:
        # Update existing lead with email if not already present
        if payload.email not in (existing_lead.emails or []):
            emails = existing_lead.emails or []
            emails.append(payload.email)
            existing_lead.emails = emails
            db.commit()
            db.refresh(existing_lead)
        
        return {
            "success": True,
            "message": "Email added to existing lead",
            "lead_id": existing_lead.id,
            "lead": {
                "id": existing_lead.id,
                "name": existing_lead.name,
                "email": payload.email,
            },
        }
    
    # Create new lead
    lead = LeadORM(
        organization_id=org.id,
        name=f"{payload.first_name} {payload.last_name}".strip(),
        website=payload.domain if not payload.domain.startswith("http") else payload.domain,
        emails=[payload.email],
        source="email_finder",
        niche=payload.company_name or "",
        city=None,
        country=None,
        quality_score=payload.confidence if payload.confidence else None,
        status=LeadStatus.new,
        job_id=payload.job_id,
    )
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    return {
        "success": True,
        "message": "Lead created successfully",
        "lead_id": lead.id,
        "lead": {
            "id": lead.id,
            "name": lead.name,
            "email": payload.email,
            "website": lead.website,
        },
    }


@router.get("/email-verifier/export/csv")
def export_verifications_csv(
    db: Session = Depends(get_db),
):
    """Export email verification results to CSV"""
    from fastapi.responses import Response
    import csv
    import io
    
    org = get_or_create_default_org(db)
    
    verifications = db.query(EmailVerificationORM).filter(
        EmailVerificationORM.organization_id == org.id
    ).order_by(EmailVerificationORM.created_at.desc()).limit(10000).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Email",
        "Status",
        "Reason",
        "Confidence",
        "SMTP Checked",
        "Checked At",
        "Created At",
    ])
    
    # Write data
    for v in verifications:
        writer.writerow([
            v.email,
            v.status.value,
            v.reason or "",
            str(v.confidence) if v.confidence else "",
            "Yes" if v.smtp_checked else "No",
            v.checked_at.isoformat() if v.checked_at else "",
            v.created_at.isoformat(),
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=email_verifications.csv"}
    )


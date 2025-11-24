"""Service for capturing leads from LinkedIn profiles"""
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.orm import (
    OrganizationORM, LeadORM, LeadStatus, EmailORM,
    EmailFinderJobORM, EmailFinderJobStatus,
)
from app.services.email_finder import find_email as find_email_service
from app.services.credit_manager import CreditManager
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)


def normalize_name(full_name: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> Tuple[str, str]:
    """
    Normalize name into first_name and last_name
    
    Returns: (first_name, last_name)
    """
    if first_name and last_name:
        return first_name.strip(), last_name.strip()
    
    if not full_name:
        return "", ""
    
    parts = full_name.strip().split()
    
    if len(parts) >= 2:
        first = first_name or parts[0]
        last = last_name or " ".join(parts[1:])
    elif len(parts) == 1:
        first = first_name or parts[0]
        last = last_name or ""
    else:
        first = first_name or ""
        last = last_name or ""
    
    return first.strip(), last.strip()


def extract_domain_from_company(company_name: Optional[str], company_domain: Optional[str] = None) -> Optional[str]:
    """Extract or normalize company domain"""
    if company_domain:
        # Clean domain (remove http://, www., etc.)
        domain = company_domain.lower().strip()
        domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
        domain = domain.split("/")[0].split("?")[0]
        return domain if domain else None
    
    if not company_name:
        return None
    
    # Simple heuristic: convert company name to domain
    # Remove common suffixes and clean
    domain = company_name.lower().strip()
    domain = domain.replace(" inc", "").replace(" llc", "").replace(" corp", "").replace(" ltd", "")
    domain = domain.replace(" ", "").replace(".", "").replace(",", "")
    
    # Limit length and add .com
    if len(domain) > 20:
        domain = domain[:20]
    
    return f"{domain}.com" if domain else None


def get_or_create_lead_from_linkedin(
    db: Session,
    organization_id: int,
    first_name: str,
    last_name: str,
    full_name: str,
    title: Optional[str] = None,
    headline: Optional[str] = None,
    company_name: Optional[str] = None,
    company_domain: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    workspace_id: Optional[int] = None,  # NEW: Added workspace_id
    owner_user_id: Optional[int] = None,  # NEW: Added owner_user_id for rep performance
) -> LeadORM:
    """
    Get or create a lead from LinkedIn profile data
    
    Checks for existing lead by LinkedIn URL or name+company
    """
    # Try to find existing lead by LinkedIn URL first
    if linkedin_url:
        existing = db.query(LeadORM).filter(
            LeadORM.organization_id == organization_id,
            LeadORM.website == linkedin_url
        ).first()
        
        if existing:
            # Update with latest info
            existing.name = full_name
            existing.contact_person_name = full_name
            existing.contact_person_role = title or headline
            if company_name:
                existing.niche = company_name
            if company_domain:
                existing.website = company_domain if not company_domain.startswith("http") else linkedin_url
            db.commit()
            db.refresh(existing)
            return existing
    
    # Try to find by name + company
    if company_name:
        existing = db.query(LeadORM).filter(
            LeadORM.organization_id == organization_id,
            LeadORM.name == full_name,
            LeadORM.niche == company_name
        ).first()
        
        if existing:
            # Update LinkedIn URL if provided
            if linkedin_url and not existing.website:
                existing.website = linkedin_url
            db.commit()
            db.refresh(existing)
            return existing
    
    # Create new lead
    domain = extract_domain_from_company(company_name, company_domain)
    website = domain if domain and not domain.startswith("http") else linkedin_url
    
    lead = LeadORM(
        organization_id=organization_id,
        workspace_id=workspace_id,  # Set workspace_id if provided
        owner_user_id=owner_user_id,  # Set owner for rep performance tracking
        created_by_user_id=owner_user_id,  # Also set created_by for fallback attribution
        name=full_name,
        contact_person_name=full_name,
        contact_person_role=title or headline,
        niche=company_name or "",
        website=website,
        source="linkedin_extension",
        status=LeadStatus.new,
    )
    
    # Store LinkedIn URL in metadata or social_links
    if linkedin_url:
        lead.social_links = lead.social_links or {}
        lead.social_links["linkedin"] = linkedin_url
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    logger.info(f"Created new lead from LinkedIn: {lead.id} - {full_name}")
    return lead


def build_email_status(db: Session, lead: LeadORM) -> Optional[dict]:
    """Build email status from lead's email records"""
    # Get primary email record
    email_record = db.query(EmailORM).filter(
        EmailORM.organization_id == lead.organization_id,
        EmailORM.lead_id == lead.id,
        EmailORM.label == "primary"
    ).order_by(EmailORM.created_at.desc()).first()
    
    if not email_record:
        # Check legacy emails field
        if lead.emails and len(lead.emails) > 0:
            email_str = lead.emails[0] if isinstance(lead.emails[0], str) else lead.emails[0].get("email", "")
            if email_str:
                return {
                    "email": email_str,
                    "status": None,
                    "reason": None,
                    "confidence": None,
                    "last_verified_at": None,
                }
        return None
    
    return {
        "email": email_record.email,
        "status": email_record.verify_status,
        "reason": email_record.verify_reason,
        "confidence": float(email_record.verify_confidence) if email_record.verify_confidence else None,
        "last_verified_at": email_record.verified_at.isoformat() if email_record.verified_at else None,
    }


def enqueue_finder_and_verifier(
    db: Session,
    organization_id: int,
    lead: LeadORM,
    skip_smtp: bool = False,
) -> Optional[EmailFinderJobORM]:
    """
    Create and enqueue an email finder job for a lead
    
    Returns the job if created, None if lead already has email
    """
    # Check if lead already has a verified email
    email_record = db.query(EmailORM).filter(
        EmailORM.organization_id == organization_id,
        EmailORM.lead_id == lead.id,
        EmailORM.verify_status == "valid"
    ).first()
    
    if email_record:
        logger.info(f"Lead {lead.id} already has verified email, skipping finder")
        return None
    
    # Extract name and domain
    first_name = lead.contact_person_name.split()[0] if lead.contact_person_name else lead.name.split()[0] if lead.name else ""
    last_name = " ".join(lead.contact_person_name.split()[1:]) if lead.contact_person_name and len(lead.contact_person_name.split()) > 1 else ""
    
    if not first_name:
        logger.warning(f"Cannot find email for lead {lead.id}: missing first name")
        return None
    
    # Extract domain from website
    domain = None
    if lead.website:
        domain = lead.website.replace("http://", "").replace("https://", "").replace("www.", "")
        domain = domain.split("/")[0].split("?")[0]
    
    if not domain:
        logger.warning(f"Cannot find email for lead {lead.id}: missing domain")
        return None
    
    # Check credits
    if not CreditManager.check_balance(db, organization_id, CreditManager.COST_EMAIL_FINDER):
        logger.warning(f"Insufficient credits for email finder for lead {lead.id}")
        return None
    
    # Try to find email immediately (synchronous for now, can be async later)
    try:
        result = find_email_service(
            first_name,
            last_name,
            domain,
            skip_smtp=skip_smtp,
            min_confidence=0.3
        )
        
        if result and hasattr(result, 'email') and result.email:
            # Create email record
            from app.core.orm import EmailVerificationStatus
            
            email_obj = EmailORM(
                organization_id=organization_id,
                lead_id=lead.id,
                email=result.email,
                label="primary",
                verify_status=EmailVerificationStatus(result.status.value) if hasattr(result.status, 'value') else EmailVerificationStatus(str(result.status)),
                verify_reason=result.reason if hasattr(result, 'reason') else None,
                verify_confidence=result.score if hasattr(result, 'score') else None,
                verified_at=datetime.utcnow(),
                found_via="finder",
            )
            db.add(email_obj)
            
            # Try to deduct credit (if credit manager is available)
            try:
                if CreditManager and hasattr(CreditManager, 'deduct_credits'):
                    cost = getattr(CreditManager, 'COST_EMAIL_FINDER', 1)
                    CreditManager.deduct_credits(
                        db, organization_id, cost,
                        feature="email_finder",
                        reference_id=email_obj.id,
                        reference_type="email",
                        description=f"LinkedIn capture: {result.email}"
                    )
            except Exception as credit_error:
                logger.warning(f"Could not deduct credits: {credit_error}")
            
            db.commit()
            db.refresh(email_obj)
            
            logger.info(f"Found email for lead {lead.id}: {email_obj.email}")
            return None  # No job needed, email found immediately
        else:
            logger.info(f"No email found for lead {lead.id}, creating finder job")
            # Could create a job here for retry later, but for now return None
            return None
            
    except Exception as e:
        logger.error(f"Error finding email for lead {lead.id}: {e}", exc_info=True)
        return None


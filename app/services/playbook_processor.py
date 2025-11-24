"""Background processor for playbook jobs"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.orm import LeadORM, EmailORM, OrganizationORM
from app.core.orm_lists import LeadListORM, LeadListLeadORM
from app.core.orm_playbooks import PlaybookJobORM, PlaybookJobStatus
from app.services.email_finder import find_email as find_email_service
from app.services.email_verifier import verify_email, VerificationStatus

logger = logging.getLogger(__name__)


def process_linkedin_campaign_playbook(db: Session, job_id: int):
    """
    Process a LinkedIn → Campaign playbook job
    
    This runs in the background and:
    1. Finds LinkedIn leads matching criteria
    2. Runs Email Finder on leads without emails
    3. Verifies all emails
    4. Creates a campaign-ready list with valid/risky emails
    """
    job = db.query(PlaybookJobORM).filter(PlaybookJobORM.id == job_id).first()
    if not job:
        logger.error(f"Playbook job {job_id} not found")
        return
    
    try:
        # Update status
        job.status = PlaybookJobStatus.running.value
        job.started_at = datetime.utcnow()
        db.commit()
        
        params = job.params
        days = params.get("days", 7)
        include_risky = params.get("include_risky", False)
        min_score = params.get("min_score", 0.0)
        list_name = params.get("list_name")
        
        # 1. Select candidate leads
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(LeadORM).filter(
            LeadORM.organization_id == job.organization_id,
            LeadORM.source == "linkedin_extension",
            LeadORM.created_at >= cutoff_date
        )
        
        if min_score > 0:
            query = query.filter(LeadORM.quality_score >= min_score)
        
        leads = query.all()
        total = len(leads)
        
        logger.info(f"Playbook {job_id}: Processing {total} LinkedIn leads from last {days} days")
        
        # Initialize counters
        processed = 0
        valid_count = 0
        risky_count = 0
        invalid_count = 0
        unknown_count = 0
        emails_found = 0
        emails_verified = 0
        credits_used = 0
        
        # 2. Process each lead
        for lead in leads:
            try:
                # Check if lead has email
                email_record = db.query(EmailORM).filter(
                    EmailORM.organization_id == job.organization_id,
                    EmailORM.lead_id == lead.id
                ).order_by(EmailORM.created_at.desc()).first()
                
                # a) If no email → run finder
                if not email_record:
                    # Extract name and domain
                    first_name = ""
                    last_name = ""
                    if lead.contact_person_name:
                        parts = lead.contact_person_name.split()
                        first_name = parts[0] if parts else ""
                        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    elif lead.name:
                        parts = lead.name.split()
                        first_name = parts[0] if parts else ""
                        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    
                    # Extract domain
                    domain = None
                    if lead.website:
                        domain = lead.website.replace("http://", "").replace("https://", "").replace("www.", "")
                        domain = domain.split("/")[0].split("?")[0]
                    
                    if first_name and domain:
                        try:
                            result = find_email_service(
                                first_name,
                                last_name,
                                domain,
                                skip_smtp=False,
                                min_confidence=0.3
                            )
                            
                            if result and result.email:
                                # Create email record
                                status_str = result.status.value if hasattr(result.status, 'value') else str(result.status)
                                email_record = EmailORM(
                                    organization_id=job.organization_id,
                                    lead_id=lead.id,
                                    email=result.email,
                                    label="primary",
                                    verify_status=status_str,
                                    verify_reason=result.reason,
                                    verify_confidence=result.score,
                                    verified_at=datetime.utcnow(),
                                    found_via="finder",
                                )
                                db.add(email_record)
                                db.commit()
                                emails_found += 1
                                credits_used += 1  # Email finder costs 1 credit
                        except Exception as e:
                            logger.warning(f"Failed to find email for lead {lead.id}: {e}")
                
                # b) If email but no status → verify
                if email_record and not email_record.verify_status:
                    try:
                        status, reason = verify_email(email_record.email, skip_smtp=False)
                        status_str = status.value if hasattr(status, 'value') else str(status)
                        email_record.verify_status = status_str
                        email_record.verify_reason = reason
                        email_record.verified_at = datetime.utcnow()
                        db.commit()
                        emails_verified += 1
                        credits_used += 1  # Email verification costs 1 credit
                    except Exception as e:
                        logger.warning(f"Failed to verify email for lead {lead.id}: {e}")
                
                # Update counters based on email status
                if email_record:
                    status = email_record.verify_status
                    if status == "valid":
                        valid_count += 1
                    elif status == "risky":
                        risky_count += 1
                    elif status == "invalid":
                        invalid_count += 1
                    elif status == "unknown":
                        unknown_count += 1
                
                processed += 1
                
                # Update progress periodically (every 10 leads)
                if processed % 10 == 0:
                    job.meta = {
                        "total_leads": total,
                        "processed_leads": processed,
                        "emails_found": emails_found,
                        "emails_verified": emails_verified,
                        "valid_count": valid_count,
                        "risky_count": risky_count,
                        "invalid_count": invalid_count,
                        "unknown_count": unknown_count,
                    }
                    job.credits_used = credits_used
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Error processing lead {lead.id}: {e}")
                continue
        
        # 3. Build output list
        if not list_name:
            week_num = datetime.utcnow().isocalendar()[1]
            list_name = f"LinkedIn – Week {week_num} – Campaign"
        
        output_list = LeadListORM(
            organization_id=job.organization_id,
            name=list_name,
            description=f"Campaign-ready leads from LinkedIn extension (last {days} days)",
            is_campaign_ready=True,
        )
        db.add(output_list)
        db.flush()
        
        # Add qualifying leads to the list
        added_count = 0
        for lead in leads:
            email_record = db.query(EmailORM).filter(
                EmailORM.organization_id == job.organization_id,
                EmailORM.lead_id == lead.id
            ).order_by(EmailORM.created_at.desc()).first()
            
            if not email_record:
                continue
            
            status = email_record.verify_status
            score = float(lead.quality_score) if lead.quality_score else 0.0
            
            qualifies = False
            if status == "valid" and score >= min_score:
                qualifies = True
            elif status == "risky" and include_risky and score >= min_score:
                qualifies = True
            
            if qualifies:
                # Check if already in list
                existing = db.query(LeadListLeadORM).filter(
                    LeadListLeadORM.list_id == output_list.id,
                    LeadListLeadORM.lead_id == lead.id
                ).first()
                
                if not existing:
                    list_lead = LeadListLeadORM(
                        list_id=output_list.id,
                        lead_id=lead.id,
                    )
                    db.add(list_lead)
                    added_count += 1
        
        db.commit()
        
        # 4. Update job with final stats
        job.status = PlaybookJobStatus.completed.value
        job.finished_at = datetime.utcnow()
        job.output_list_id = output_list.id
        job.meta = {
            "total_leads": total,
            "processed_leads": processed,
            "emails_found": emails_found,
            "emails_verified": emails_verified,
            "valid_count": valid_count,
            "risky_count": risky_count,
            "invalid_count": invalid_count,
            "unknown_count": unknown_count,
            "output_list_id": output_list.id,
            "output_list_name": list_name,
            "leads_added_to_list": added_count,
        }
        job.credits_used = credits_used
        db.commit()
        
        logger.info(f"Playbook {job_id} completed: {added_count} leads added to list {output_list.id}")
        
    except Exception as e:
        logger.error(f"Playbook job {job_id} failed: {e}", exc_info=True)
        job.status = PlaybookJobStatus.failed.value
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()


def estimate_playbook_credits(db: Session, organization_id: int, days: int, min_score: float = 0.0) -> int:
    """
    Estimate credits needed for a playbook run
    
    Returns estimated credit cost
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(LeadORM).filter(
        LeadORM.organization_id == organization_id,
        LeadORM.source == "linkedin_extension",
        LeadORM.created_at >= cutoff_date
    )
    
    if min_score > 0:
        query = query.filter(LeadORM.quality_score >= min_score)
    
    total_leads = query.count()
    
    # Count leads without emails (will need finder)
    leads_without_email = db.query(LeadORM).filter(
        LeadORM.organization_id == organization_id,
        LeadORM.source == "linkedin_extension",
        LeadORM.created_at >= cutoff_date,
        ~LeadORM.id.in_(
            db.query(EmailORM.lead_id).filter(
                EmailORM.organization_id == organization_id
            )
        )
    )
    
    if min_score > 0:
        leads_without_email = leads_without_email.filter(LeadORM.quality_score >= min_score)
    
    leads_needing_finder = leads_without_email.count()
    
    # Count leads with emails but no status (will need verification)
    leads_with_email_no_status = db.query(LeadORM).join(
        EmailORM, LeadORM.id == EmailORM.lead_id
    ).filter(
        LeadORM.organization_id == organization_id,
        LeadORM.source == "linkedin_extension",
        LeadORM.created_at >= cutoff_date,
        EmailORM.organization_id == organization_id,
        EmailORM.verify_status.is_(None)
    )
    
    if min_score > 0:
        leads_with_email_no_status = leads_with_email_no_status.filter(LeadORM.quality_score >= min_score)
    
    leads_needing_verify = leads_with_email_no_status.count()
    
    # Estimate: 1 credit per finder, 1 credit per verification
    estimated = leads_needing_finder + leads_needing_verify
    
    return estimated


"""Company search service - finds people at companies"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.orm import LeadORM, OrganizationORM
from app.core.orm_companies import CompanyORM
from app.core.orm_company_search import CompanySearchJobORM, CompanySearchJobStatus
from app.core.orm_lists import LeadListORM, LeadListLeadORM
from app.services.email_finder import find_email as find_email_service
from app.services.email_verifier import verify_email, VerificationStatus

logger = logging.getLogger(__name__)


def normalize_domain(domain_or_name: str) -> str:
    """Normalize domain or company name to domain"""
    domain = domain_or_name.strip().lower()
    
    # Remove protocol
    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.replace("www.", "")
    
    # Extract domain from URL
    if "/" in domain:
        domain = domain.split("/")[0]
    if "?" in domain:
        domain = domain.split("?")[0]
    
    return domain


def get_or_create_company(
    db: Session,
    organization_id: int,
    name: str,
    domain: Optional[str] = None,
    **kwargs
) -> CompanyORM:
    """Get or create a company"""
    if not domain:
        domain = normalize_domain(name)
    
    # Try to find by domain first
    company = db.query(CompanyORM).filter(
        CompanyORM.domain == domain
    ).first()
    
    if company:
        # Update with new info
        if name and not company.name:
            company.name = name
        for key, value in kwargs.items():
            if value and hasattr(company, key):
                setattr(company, key, value)
        db.commit()
        db.refresh(company)
        return company
    
    # Try to find by name
    company = db.query(CompanyORM).filter(
        CompanyORM.name.ilike(f"%{name}%")
    ).first()
    
    if company:
        # Update domain if provided
        if domain and not company.domain:
            company.domain = domain
        db.commit()
        db.refresh(company)
        return company
    
    # Create new company
    company = CompanyORM(
        name=name,
        domain=domain,
        **kwargs
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def find_people_at_company(
    company_name: str,
    domain: str,
    roles: List[str],
    min_company_size: Optional[int] = None,
    max_company_size: Optional[int] = None,
    country: Optional[str] = None,
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Find people at a company
    
    This is a placeholder implementation. In production, you would:
    1. Use LinkedIn API (if available)
    2. Use Clearbit/FullContact APIs
    3. Use Hunter.io or similar
    4. Use internal database if you have company data
    
    For now, returns mock data structure that matches what we expect.
    """
    # TODO: Integrate with real data sources
    # For MVP, we'll create leads based on common patterns
    
    people = []
    
    # Mock implementation - in production, call external APIs
    # Example structure:
    # people = [
    #     {
    #         "first_name": "John",
    #         "last_name": "Doe",
    #         "title": "CEO",
    #         "linkedin_url": "https://linkedin.com/in/johndoe",
    #         "company_name": company_name,
    #         "domain": domain,
    #     },
    #     ...
    # ]
    
    logger.warning(f"Company search using mock data for {company_name}. Integrate real data sources in production.")
    
    return people


def process_company_search_job(db: Session, job_id: int):
    """Process a company search job"""
    job = db.query(CompanySearchJobORM).filter(CompanySearchJobORM.id == job_id).first()
    if not job:
        logger.error(f"Company search job {job_id} not found")
        return
    
    try:
        job.status = CompanySearchJobStatus.running.value
        job.started_at = datetime.utcnow()
        db.commit()
        
        params = job.params
        query = params.get("query", "")
        roles = params.get("roles", [])
        min_company_size = params.get("min_company_size")
        max_company_size = params.get("max_company_size")
        country = params.get("country")
        list_name = params.get("list_name")
        max_leads = params.get("max_leads", 50)
        
        # Normalize domain
        domain = normalize_domain(query)
        company_name = query if "." not in query else domain.split(".")[0].title()
        
        # Get or create company
        company = get_or_create_company(
            db=db,
            organization_id=job.organization_id,
            name=company_name,
            domain=domain,
            country=country,
        )
        job.company_id = company.id
        db.commit()
        
        # Find people at company
        people = find_people_at_company(
            company_name=company_name,
            domain=domain,
            roles=roles,
            min_company_size=min_company_size,
            max_company_size=max_company_size,
            country=country,
            max_results=max_leads
        )
        
        if not people:
            logger.warning(f"No people found for company {company_name}")
            job.status = CompanySearchJobStatus.completed.value
            job.finished_at = datetime.utcnow()
            job.meta = {
                "estimated_leads": 0,
                "leads_found": 0,
                "emails_found": 0,
                "emails_verified": 0,
            }
            db.commit()
            return
        
        # Create list name if not provided
        if not list_name:
            list_name = f"{company_name} – Decision Makers"
        
        output_list = LeadListORM(
            organization_id=job.organization_id,
            name=list_name,
            description=f"Leads from company search: {company_name}",
            is_campaign_ready=False,  # Will be marked ready after verification
        )
        db.add(output_list)
        db.flush()
        
        # Process each person
        leads_created = 0
        emails_found = 0
        emails_verified = 0
        
        for person in people[:max_leads]:
            try:
                # Create or get lead
                first_name = person.get("first_name", "")
                last_name = person.get("last_name", "")
                full_name = f"{first_name} {last_name}".strip()
                title = person.get("title", "")
                linkedin_url = person.get("linkedin_url")
                
                if not full_name:
                    continue
                
                # Check if lead already exists
                existing_lead = db.query(LeadORM).filter(
                    LeadORM.organization_id == job.organization_id,
                    LeadORM.company_id == company.id,
                    LeadORM.contact_person_name == full_name
                ).first()
                
                if existing_lead:
                    lead = existing_lead
                else:
                    lead = LeadORM(
                        organization_id=job.organization_id,
                        name=full_name,
                        contact_person_name=full_name,
                        contact_person_role=title,
                        company_id=company.id,
                        website=domain,
                        linkedin_url=linkedin_url,
                        source="company_search",
                        status="new",
                    )
                    db.add(lead)
                    db.flush()
                    leads_created += 1
                
                # Run email finder
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
                            from app.core.orm import EmailORM
                            # Check if email already exists
                            existing_email = db.query(EmailORM).filter(
                                EmailORM.organization_id == job.organization_id,
                                EmailORM.lead_id == lead.id,
                                EmailORM.email == result.email
                            ).first()
                            
                            if not existing_email:
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
                                emails_found += 1
                                emails_verified += 1
                    except Exception as e:
                        logger.warning(f"Failed to find email for {full_name}: {e}")
                
                # Add to list
                existing_list_lead = db.query(LeadListLeadORM).filter(
                    LeadListLeadORM.list_id == output_list.id,
                    LeadListLeadORM.lead_id == lead.id
                ).first()
                
                if not existing_list_lead:
                    list_lead = LeadListLeadORM(
                        list_id=output_list.id,
                        lead_id=lead.id,
                    )
                    db.add(list_lead)
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Error processing person: {e}")
                continue
        
        # Mark list as campaign-ready if we have valid emails
        if emails_verified > 0:
            output_list.is_campaign_ready = True
            db.commit()
        
        # Update job
        job.status = CompanySearchJobStatus.completed.value
        job.finished_at = datetime.utcnow()
        job.output_list_id = output_list.id
        job.meta = {
            "estimated_leads": len(people),
            "leads_found": leads_created,
            "emails_found": emails_found,
            "emails_verified": emails_verified,
            "list_id": output_list.id,
            "list_name": list_name,
        }
        db.commit()
        
        logger.info(f"Company search job {job_id} completed: {leads_created} leads, {emails_found} emails")
        
    except Exception as e:
        logger.error(f"Company search job {job_id} failed: {e}", exc_info=True)
        job.status = CompanySearchJobStatus.failed.value
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()


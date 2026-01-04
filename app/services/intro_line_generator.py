"""AI-powered intro line generator for leads"""
import logging
import os
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.orm import LeadORM
from app.core.orm_companies import CompanyORM

logger = logging.getLogger(__name__)


def _env_truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def llm_enabled() -> bool:
    """
    LLM features are disabled by default so the API can run without Groq/OpenAI/Anthropic.

    Enable explicitly with:
      - ENABLE_LLM=1

    Force-disable with:
      - DISABLE_LLM=1
    """
    if _env_truthy(os.getenv("DISABLE_LLM")):
        return False
    return _env_truthy(os.getenv("ENABLE_LLM"))


def generate_intro_line_for_lead(
    db: Session,
    lead: LeadORM,
    regenerate: bool = False
) -> Optional[str]:
    """
    Generate a personalized intro line for a lead using AI
    
    Args:
        db: Database session
        lead: Lead to generate intro for
        regenerate: If True, regenerate even if intro_line exists
    
    Returns:
        Generated intro line or None if failed
    """
    # Skip if already generated and not regenerating
    if lead.intro_line and not regenerate:
        return lead.intro_line

    if not llm_enabled():
        logger.info("Intro line generation skipped (LLM disabled).")
        return None
    
    try:
        # Build context from lead and company
        context_parts = []
        
        if lead.contact_person_name:
            context_parts.append(f"Name: {lead.contact_person_name}")
        if lead.contact_person_role:
            context_parts.append(f"Role: {lead.contact_person_role}")
        if lead.name:
            context_parts.append(f"Business: {lead.name}")
        
        # Get company info if available
        company = None
        if lead.company_id:
            company = db.query(CompanyORM).filter(CompanyORM.id == lead.company_id).first()
        
        if company:
            if company.name:
                context_parts.append(f"Company: {company.name}")
            if company.industry:
                context_parts.append(f"Industry: {company.industry}")
            if company.size:
                context_parts.append(f"Company size: {company.size}")
            if company.country:
                context_parts.append(f"Location: {company.country}")
        
        if lead.niche:
            context_parts.append(f"Niche: {lead.niche}")
        if lead.city:
            context_parts.append(f"City: {lead.city}")
        if lead.website:
            context_parts.append(f"Website: {lead.website}")
        
        context = "\n".join(context_parts)
        
        # Build prompt
        prompt = f"""Generate a personalized, warm first line for an outreach email to this person. 
The line should be:
- Short (one sentence, max 20 words)
- Specific to their role/company/industry
- Warm and human (not robotic)
- Professional but friendly

Context:
{context}

Generate only the first line, nothing else. Do not include quotes or formatting."""

        # LLM integration is intentionally disabled by default.
        # If you want to enable it, implement a provider adapter in this module.
        logger.warning("LLM is enabled, but intro line LLM adapter is not implemented.")
        return None
        
    except Exception as e:
        logger.error(f"Failed to generate intro line for lead {lead.id}: {e}", exc_info=True)
        return None


def generate_intro_lines_for_list(
    db: Session,
    organization_id: int,
    list_id: int,
    regenerate: bool = False
) -> dict:
    """
    Generate intro lines for all leads in a list (background job)
    
    Returns:
        Dict with counts: {total, generated, failed}
    """
    from app.core.orm_lists import LeadListORM, LeadListLeadORM
    
    lead_list = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == organization_id
    ).first()
    
    if not lead_list:
        raise ValueError(f"List {list_id} not found")
    
    # Get all leads in list
    list_leads = db.query(LeadListLeadORM).filter(
        LeadListLeadORM.list_id == list_id
    ).all()
    
    total = len(list_leads)
    generated = 0
    failed = 0
    
    for list_lead in list_leads:
        lead = db.query(LeadORM).filter(LeadORM.id == list_lead.lead_id).first()
        if not lead:
            continue
        
        # Skip if already has intro line and not regenerating
        if lead.intro_line and not regenerate:
            continue
        
        try:
            result = generate_intro_line_for_lead(db, lead, regenerate=regenerate)
            if result:
                generated += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Failed to generate intro line for lead {lead.id}: {e}")
            failed += 1
    
    return {
        "total": total,
        "generated": generated,
        "failed": failed,
    }


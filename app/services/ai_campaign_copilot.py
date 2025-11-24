"""AI Campaign Copilot: Template generation and A/B test optimization"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.orm_campaigns import CampaignORM, CampaignTemplateORM, TemplateType
from app.core.orm_segments import SegmentORM
from app.core.orm_lists import LeadListORM
from app.core.orm import LeadORM
# Import LLM client factory
from app.ai.factory import create_llm_client

logger = logging.getLogger(__name__)


def generate_segment_summary(
    db: Session,
    segment: Optional[SegmentORM] = None,
    list_obj: Optional[LeadListORM] = None,
    organization_id: int = None,
    workspace_id: Optional[int] = None,
) -> str:
    """
    Generate a summary of the target audience for AI prompt context
    """
    summary_parts = []
    
    if segment:
        summary_parts.append(f"Segment: {segment.name}")
        if segment.description:
            summary_parts.append(f"Description: {segment.description}")
        
        # Analyze segment filters
        if segment.filter_json:
            filters = segment.filter_json
            if filters.get("countries"):
                summary_parts.append(f"Regions: {', '.join(filters['countries'])}")
            if filters.get("roles_contains"):
                summary_parts.append(f"Target roles: {', '.join(filters['roles_contains'])}")
            if filters.get("min_score"):
                summary_parts.append(f"Min lead score: {filters['min_score']}")
    
    if list_obj:
        summary_parts.append(f"List: {list_obj.name}")
        # Get sample leads to infer characteristics
        sample_leads = db.query(LeadORM).filter(
            LeadORM.organization_id == organization_id,
            LeadORM.workspace_id == workspace_id if workspace_id else True,
        ).join(
            "list_memberships"
        ).filter(
            "list_memberships.list_id == list_obj.id"
        ).limit(10).all()
        
        if sample_leads:
            roles = [l.contact_person_role for l in sample_leads if l.contact_person_role]
            if roles:
                unique_roles = list(set(roles))[:5]
                summary_parts.append(f"Common roles: {', '.join(unique_roles)}")
            
            niches = [l.niche for l in sample_leads if l.niche]
            if niches:
                unique_niches = list(set(niches))[:3]
                summary_parts.append(f"Industries: {', '.join(unique_niches)}")
    
    return "\n".join(summary_parts) if summary_parts else "General B2B audience"


def generate_ai_templates(
    db: Session,
    campaign: CampaignORM,
    *,
    num_subjects: int = 3,
    num_bodies: int = 2,
    tone: str = "friendly",
    goal: str = "start a conversation",
    offer: Optional[str] = None,
) -> Dict[str, List[CampaignTemplateORM]]:
    """
    Generate AI email templates (subjects and bodies) for a campaign
    
    Returns:
        Dict with 'subjects' and 'bodies' lists of CampaignTemplateORM objects
    """
    # Get segment/list context
    segment = campaign.segment
    list_obj = campaign.list
    
    # Generate audience summary
    audience_summary = generate_segment_summary(
        db=db,
        segment=segment,
        list_obj=list_obj,
        organization_id=campaign.organization_id,
        workspace_id=campaign.workspace_id,
    )
    
    # Build prompt
    system_prompt = """You are an expert B2B email copywriter. Generate email templates that are:
- Concise and scannable
- Personalized and relevant
- Clear call-to-action
- Professional but approachable
- Avoid spam triggers

Return ONLY valid JSON with this structure:
{
  "subjects": ["Subject line 1", "Subject line 2", ...],
  "bodies": ["Email body 1", "Email body 2", ...]
}"""

    user_prompt = f"""Generate {num_subjects} subject lines and {num_bodies} email bodies for a B2B outreach campaign.

Target Audience:
{audience_summary}

Tone: {tone}
Goal: {goal}
{"Offer: " + offer if offer else ""}

Subject lines should be:
- 50 characters or less
- Intriguing but not clickbait
- Relevant to the audience

Email bodies should be:
- 100-200 words
- Start with a brief personalization
- Clearly state the value proposition
- Include a soft call-to-action
- End with a professional signature placeholder

Return JSON only, no markdown formatting."""

    try:
        # Use LLM client factory (supports Groq, OpenAI, Anthropic)
        llm_client = create_llm_client()
        if not llm_client:
            raise ValueError("No LLM client available. Set GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
        
        # For async clients, we need to handle differently
        # For now, use Groq sync client directly if available
        import os
        from groq import Groq
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            response_format={"type": "json_object"},
        )
        
        result = response.choices[0].message.content
        import json
        data = json.loads(result)
        
        subjects_data = data.get("subjects", [])
        bodies_data = data.get("bodies", [])
        
        # Create template objects
        subjects = []
        for i, content in enumerate(subjects_data[:num_subjects], 1):
            template = CampaignTemplateORM(
                workspace_id=campaign.workspace_id,
                campaign_id=campaign.id,
                type=TemplateType.subject,
                name=f"Subject {chr(64 + i)}",  # A, B, C, ...
                content=content,
                ai_generated=True,
                created_by_user_id=campaign.created_by_user_id,
            )
            db.add(template)
            subjects.append(template)
        
        bodies = []
        for i, content in enumerate(bodies_data[:num_bodies], 1):
            template = CampaignTemplateORM(
                workspace_id=campaign.workspace_id,
                campaign_id=campaign.id,
                type=TemplateType.body,
                name=f"Body v{i}",
                content=content,
                ai_generated=True,
                created_by_user_id=campaign.created_by_user_id,
            )
            db.add(template)
            bodies.append(template)
        
        db.commit()
        
        # Refresh to get IDs
        for template in subjects + bodies:
            db.refresh(template)
        
        logger.info(f"Generated {len(subjects)} subjects and {len(bodies)} bodies for campaign {campaign.id}")
        
        return {
            "subjects": subjects,
            "bodies": bodies,
        }
        
    except Exception as e:
        logger.error(f"Error generating AI templates: {e}", exc_info=True)
        db.rollback()
        raise


def get_template_performance(
    db: Session,
    campaign: CampaignORM,
) -> Dict[str, Any]:
    """
    Calculate performance metrics for each template variant
    
    Returns:
        Dict with 'subjects' and 'bodies' lists, each containing template stats
    """
    from sqlalchemy import func, case
    
    # Get all templates for this campaign
    templates = db.query(CampaignTemplateORM).filter(
        CampaignTemplateORM.campaign_id == campaign.id
    ).all()
    
    subjects = [t for t in templates if t.type == TemplateType.subject]
    bodies = [t for t in templates if t.type == TemplateType.body]
    
    # Calculate stats for subjects
    subject_stats = []
    for template in subjects:
        stats = db.query(
            func.count(CampaignLeadORM.id).label("sent"),
            func.sum(case((CampaignLeadORM.opened == True, 1), else_=0)).label("opened"),
            func.sum(case((CampaignLeadORM.clicked == True, 1), else_=0)).label("clicked"),
            func.sum(case((CampaignLeadORM.replied == True, 1), else_=0)).label("replied"),
        ).filter(
            CampaignLeadORM.campaign_id == campaign.id,
            CampaignLeadORM.subject_template_id == template.id,
            CampaignLeadORM.sent == True,
        ).first()
        
        sent = stats.sent or 0
        opened = stats.opened or 0
        clicked = stats.clicked or 0
        replied = stats.replied or 0
        
        open_rate = (opened / sent * 100) if sent > 0 else 0.0
        click_rate = (clicked / sent * 100) if sent > 0 else 0.0
        reply_rate = (replied / sent * 100) if sent > 0 else 0.0
        
        subject_stats.append({
            "id": template.id,
            "name": template.name,
            "content": template.content,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "reply_rate": round(reply_rate, 2),
        })
    
    # Calculate stats for bodies
    body_stats = []
    for template in bodies:
        stats = db.query(
            func.count(CampaignLeadORM.id).label("sent"),
            func.sum(case((CampaignLeadORM.opened == True, 1), else_=0)).label("opened"),
            func.sum(case((CampaignLeadORM.clicked == True, 1), else_=0)).label("clicked"),
            func.sum(case((CampaignLeadORM.replied == True, 1), else_=0)).label("replied"),
        ).filter(
            CampaignLeadORM.campaign_id == campaign.id,
            CampaignLeadORM.body_template_id == template.id,
            CampaignLeadORM.sent == True,
        ).first()
        
        sent = stats.sent or 0
        opened = stats.opened or 0
        clicked = stats.clicked or 0
        replied = stats.replied or 0
        
        open_rate = (opened / sent * 100) if sent > 0 else 0.0
        click_rate = (clicked / sent * 100) if sent > 0 else 0.0
        reply_rate = (replied / sent * 100) if sent > 0 else 0.0
        
        body_stats.append({
            "id": template.id,
            "name": template.name,
            "content": template.content,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "reply_rate": round(reply_rate, 2),
        })
    
    # Find winners
    best_subject = max(subject_stats, key=lambda x: x["open_rate"]) if subject_stats else None
    best_body = max(body_stats, key=lambda x: x["reply_rate"]) if body_stats else None
    
    return {
        "subjects": subject_stats,
        "bodies": body_stats,
        "best_subject": best_subject,
        "best_body": best_body,
    }


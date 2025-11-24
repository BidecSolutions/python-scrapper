"""AI Playbook Builder: Generate playbook blueprints from natural language"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.orm_ai_playbook import AIPlaybookBlueprintORM, PlaybookBlueprintStatus
from app.core.orm_segments import SegmentORM
from app.services.ai_campaign_copilot import generate_ai_templates
from app.core.orm_campaigns import CampaignORM

logger = logging.getLogger(__name__)


def generate_playbook_blueprint(
    db: Session,
    user_prompt: str,
    workspace_id: int,
    organization_id: int,
    created_by_user_id: int,
    tone: str = "friendly",
    workspace_language: str = "en",
) -> Dict[str, Any]:
    """
    Generate a playbook blueprint from natural language prompt using LLM
    
    Returns:
        Dict with blueprint JSON structure
    """
    # Build system prompt
    system_prompt = """You are an expert B2B sales automation consultant. Generate detailed playbook blueprints from user descriptions.

A playbook blueprint defines:
1. Segment definition (target audience filters)
2. Data sources to use (linkedin_extension, company_search, csv)
3. Pipeline steps (capture, enrich, filter, build_list, create_campaign, nba_tasks)
4. Targets (meetings, reply_rate_min, etc.)

Return ONLY valid JSON with this exact structure:
{
  "name": "Playbook name",
  "segment": {
    "name": "Segment name",
    "filter": {
      "countries": ["United States"],
      "industry_contains": ["saas", "software"],
      "roles_contains": ["founder", "ceo"],
      "company_size": ["2-10", "11-50"],
      "min_score": 70
    }
  },
  "data_sources": ["linkedin_extension", "company_search"],
  "pipeline": [
    {"type": "capture", "source": "linkedin_extension"},
    {"type": "company_search", "max_leads_per_week": 200},
    {"type": "enrich_and_verify", "finder": true, "verifier": true},
    {"type": "filter", "min_score": 70, "exclude_suppressed": true},
    {"type": "build_list", "list_name": "Campaign List"},
    {"type": "create_campaign", "campaign_name": "Campaign Name", "ai_templates": {"num_subjects": 3, "num_bodies": 2, "tone": "friendly", "goal": "book calls"}},
    {"type": "nba_tasks_for_replies", "action": "schedule_follow_up"}
  ],
  "targets": {
    "meetings": 10,
    "reply_rate_min": 0.08
  }
}"""

    user_prompt_enhanced = f"""Generate a playbook blueprint for this request:

"{user_prompt}"

Tone: {tone}
Language: {workspace_language}

Extract:
- Target audience (countries, industries, roles, company sizes)
- Data sources needed (LinkedIn, company search, CSV)
- Pipeline steps (capture, enrich, filter, build list, create campaign, tasks)
- Goals/targets (meetings, reply rates, etc.)

Return JSON only, no markdown formatting."""

    try:
        # Use Groq LLM
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
                {"role": "user", "content": user_prompt_enhanced},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        
        result = response.choices[0].message.content
        blueprint_json = json.loads(result)
        
        # Validate blueprint structure
        if not isinstance(blueprint_json, dict):
            raise ValueError("Blueprint must be a JSON object")
        
        # Ensure required fields
        if "name" not in blueprint_json:
            blueprint_json["name"] = f"Playbook - {datetime.utcnow().strftime('%Y-%m-%d')}"
        
        if "segment" not in blueprint_json:
            raise ValueError("Blueprint must include 'segment' definition")
        
        if "pipeline" not in blueprint_json:
            raise ValueError("Blueprint must include 'pipeline' steps")
        
        logger.info(f"Generated playbook blueprint: {blueprint_json.get('name')}")
        
        return blueprint_json
        
    except Exception as e:
        logger.error(f"Error generating playbook blueprint: {e}", exc_info=True)
        raise


def execute_playbook_blueprint(
    db: Session,
    blueprint: AIPlaybookBlueprintORM,
    workspace_id: int,
    organization_id: int,
    created_by_user_id: int,
) -> Dict[str, Any]:
    """
    Execute a playbook blueprint: create segment, playbook, campaign, etc.
    
    Returns:
        Dict with created resources (segment_id, playbook_id, campaign_id, list_id)
    """
    blueprint_json = blueprint.blueprint_json
    results = {
        "segment_id": None,
        "playbook_id": None,
        "campaign_id": None,
        "list_id": None,
    }
    
    try:
        # 1. Create Segment
        segment_def = blueprint_json.get("segment", {})
        if segment_def:
            from app.core.orm_segments import SegmentORM
            
            segment = SegmentORM(
                workspace_id=workspace_id,
                organization_id=organization_id,
                user_id=created_by_user_id,
                name=segment_def.get("name", "AI Generated Segment"),
                description=f"Generated from playbook: {blueprint.name}",
                filter_json=segment_def.get("filter", {}),
            )
            db.add(segment)
            db.flush()
            results["segment_id"] = segment.id
            blueprint.segment_id = segment.id
            
            logger.info(f"Created segment: {segment.id} - {segment.name}")
        
        # 2. Create List (if specified in pipeline)
        list_name = None
        for step in blueprint_json.get("pipeline", []):
            if step.get("type") == "build_list":
                list_name = step.get("list_name")
                break
        
        if list_name:
            from app.core.orm_lists import LeadListORM
            
            lead_list = LeadListORM(
                workspace_id=workspace_id,
                organization_id=organization_id,
                created_by_user_id=created_by_user_id,
                name=list_name,
                description=f"Generated from playbook: {blueprint.name}",
            )
            db.add(lead_list)
            db.flush()
            results["list_id"] = lead_list.id
            blueprint.list_id = lead_list.id
            
            logger.info(f"Created list: {lead_list.id} - {lead_list.name}")
        
        # 3. Create Campaign (if specified in pipeline)
        campaign_def = None
        for step in blueprint_json.get("pipeline", []):
            if step.get("type") == "create_campaign":
                campaign_def = step
                break
        
        if campaign_def:
            from app.core.orm_campaigns import CampaignORM, CampaignStatus
            
            campaign = CampaignORM(
                workspace_id=workspace_id,
                organization_id=organization_id,
                created_by_user_id=created_by_user_id,
                name=campaign_def.get("campaign_name", "AI Generated Campaign"),
                description=f"Generated from playbook: {blueprint.name}",
                status=CampaignStatus.draft,
                segment_id=results["segment_id"],
                list_id=results["list_id"],
            )
            db.add(campaign)
            db.flush()
            results["campaign_id"] = campaign.id
            blueprint.campaign_id = campaign.id
            
            # Generate AI templates if specified
            ai_templates = campaign_def.get("ai_templates")
            if ai_templates:
                try:
                    generate_ai_templates(
                        db=db,
                        campaign=campaign,
                        num_subjects=ai_templates.get("num_subjects", 3),
                        num_bodies=ai_templates.get("num_bodies", 2),
                        tone=ai_templates.get("tone", "friendly"),
                        goal=ai_templates.get("goal", "start a conversation"),
                        offer=ai_templates.get("offer"),
                    )
                    logger.info(f"Generated AI templates for campaign: {campaign.id}")
                except Exception as e:
                    logger.warning(f"Failed to generate AI templates: {e}")
            
            logger.info(f"Created campaign: {campaign.id} - {campaign.name}")
        
        # 4. Create Playbook Job record (simplified - just stores blueprint)
        # In a full implementation, this would create a PlaybookJobORM
        # For now, we just mark the blueprint as executed
        
        blueprint.status = PlaybookBlueprintStatus.completed
        blueprint.executed_at = datetime.utcnow()
        db.add(blueprint)
        db.commit()
        
        logger.info(f"Executed playbook blueprint: {blueprint.id}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error executing playbook blueprint: {e}", exc_info=True)
        db.rollback()
        blueprint.status = PlaybookBlueprintStatus.cancelled
        db.commit()
        raise


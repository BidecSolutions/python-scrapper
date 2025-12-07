"""Services for creating Saved Views and Playbooks from AI segments"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.core.orm_saved_views import SavedViewORM
from app.core.orm_ai_playbook import AIPlaybookBlueprintORM, PlaybookBlueprintStatus
from app.core.orm import ScrapeJobORM

logger = logging.getLogger(__name__)


def create_saved_view_from_ai_segment(
    db: Session,
    *,
    org_id: int,
    workspace_id: Optional[int],
    user_id: Optional[int],
    job: ScrapeJobORM,
    segment: dict,
    segment_index: int,
) -> SavedViewORM:
    """
    Create a Saved View from an AI segment.
    
    MVP: Filters by job_id only. Later can add more sophisticated filters.
    """
    # Build name: "Job: dentist newyork – Segment: High-intent NYC clinics"
    job_name = f"{job.niche}{' - ' + job.location if job.location else ''}"
    segment_name = segment.get("name", f"Segment #{segment_index + 1}")
    view_name = f"{job_name} – {segment_name}"
    
    # Truncate to max length
    if len(view_name) > 150:
        view_name = view_name[:147] + "..."
    
    # Description from segment
    description = segment.get("description") or segment.get("ideal_use_case") or ""
    if len(description) > 500:
        description = description[:497] + "..."
    
    # MVP filters: filter by job_id only
    # Later: can add country, niche, tags, quality_score, etc. based on segment description
    filters = {
        "job_id": job.id,
        "ai_segment_index": segment_index,  # Metadata for reference
    }
    
    view = SavedViewORM(
        organization_id=org_id,
        workspace_id=workspace_id,
        user_id=user_id,
        page_type="leads",
        name=view_name,
        filters=filters,
        is_shared=True,  # Org-wide by default
        is_pinned=False,
    )
    
    db.add(view)
    db.commit()
    db.refresh(view)
    
    logger.info(f"Created saved view {view.id} from AI segment {segment_index} of job {job.id}")
    return view


def create_playbook_from_ai_segment(
    db: Session,
    *,
    org_id: int,
    workspace_id: Optional[int],
    user_id: Optional[int],
    job: ScrapeJobORM,
    segment: dict,
    segment_index: int,
) -> AIPlaybookBlueprintORM:
    """
    Create a Playbook Blueprint from an AI segment.
    
    Prefills name, description, and targeting based on segment.
    """
    # Name from segment
    name = segment.get("name") or f"{job.niche} segment #{segment_index + 1}"
    if len(name) > 150:
        name = name[:147] + "..."
    
    # Description combines segment description and ideal use case
    description_parts = []
    if segment.get("description"):
        description_parts.append(segment["description"])
    if segment.get("ideal_use_case"):
        description_parts.append(f"Use case: {segment['ideal_use_case']}")
    
    description = "\n\n".join(description_parts) if description_parts else ""
    if len(description) > 500:
        description = description[:497] + "..."
    
    # User prompt (what the AI segment represents)
    user_prompt = f"Create a playbook for: {segment.get('name', 'this segment')} from job '{job.niche}{' - ' + job.location if job.location else ''}'. {segment.get('description', '')}"
    
    # Blueprint JSON - MVP structure
    # Later: can expand this with actual automation steps, targeting rules, etc.
    blueprint_json = {
        "version": "1.0",
        "name": name,
        "description": description,
        "targeting": {
            "job_id": job.id,
            "ai_segment_index": segment_index,
        },
        "steps": [],  # Empty for now - user can add steps later
        "metadata": {
            "created_from": "ai_segment",
            "source_job_id": job.id,
            "segment_index": segment_index,
        }
    }
    
    # Get or create a default workspace if none provided
    if not workspace_id:
        from app.core.orm_workspaces import WorkspaceORM
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.organization_id == org_id
        ).first()
        if workspace:
            workspace_id = workspace.id
    
    # Workspace is required for AIPlaybookBlueprintORM
    if not workspace_id:
        raise ValueError(f"No workspace found for organization {org_id}. Cannot create playbook.")
    
    playbook = AIPlaybookBlueprintORM(
        organization_id=org_id,
        workspace_id=workspace_id,
        name=name,
        description=description,
        user_prompt=user_prompt,
        blueprint_json=blueprint_json,
        status=PlaybookBlueprintStatus.draft,
        created_by_user_id=user_id,
    )
    
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    
    logger.info(f"Created playbook blueprint {playbook.id} from AI segment {segment_index} of job {job.id}")
    return playbook


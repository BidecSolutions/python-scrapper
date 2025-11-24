"""AI Playbook Builder API routes"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.core.orm_ai_playbook import AIPlaybookBlueprintORM, PlaybookBlueprintStatus
from app.services.ai_playbook_builder import generate_playbook_blueprint, execute_playbook_blueprint

logger = logging.getLogger(__name__)
router = APIRouter()


class DraftPlaybookRequest(BaseModel):
    prompt: str = Field(..., description="Natural language description of the playbook")
    tone: str = Field("friendly", description="Tone for AI generation")
    workspace_language: str = Field("en", description="Language for AI generation")


class BlueprintOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_prompt: str
    blueprint_json: Dict[str, Any]
    status: str
    segment_id: Optional[int]
    playbook_id: Optional[int]
    campaign_id: Optional[int]
    list_id: Optional[int]
    created_at: str
    executed_at: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/ai-playbooks/draft", response_model=BlueprintOut)
def draft_ai_playbook(
    request: DraftPlaybookRequest = Body(...),
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Generate a playbook blueprint from natural language prompt
    """
    org = get_or_create_default_org(db)
    
    # TODO: Get workspace from context or parameter
    if not workspace_id:
        from app.core.orm_workspaces import WorkspaceORM
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.organization_id == org.id
        ).first()
        if workspace:
            workspace_id = workspace.id
    
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Workspace required")
    
    try:
        # Generate blueprint
        blueprint_json = generate_playbook_blueprint(
            db=db,
            user_prompt=request.prompt,
            workspace_id=workspace_id,
            organization_id=org.id,
            created_by_user_id=current_user_id,
            tone=request.tone,
            workspace_language=request.workspace_language,
        )
        
        # Save blueprint
        blueprint = AIPlaybookBlueprintORM(
            workspace_id=workspace_id,
            organization_id=org.id,
            created_by_user_id=current_user_id,
            name=blueprint_json.get("name", "AI Generated Playbook"),
            description=f"Generated from: {request.prompt[:200]}",
            user_prompt=request.prompt,
            blueprint_json=blueprint_json,
            status=PlaybookBlueprintStatus.draft,
        )
        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)
        
        return BlueprintOut(
            id=blueprint.id,
            name=blueprint.name,
            description=blueprint.description,
            user_prompt=blueprint.user_prompt,
            blueprint_json=blueprint.blueprint_json,
            status=blueprint.status.value,
            segment_id=blueprint.segment_id,
            playbook_id=blueprint.playbook_id,
            campaign_id=blueprint.campaign_id,
            list_id=blueprint.list_id,
            created_at=blueprint.created_at.isoformat(),
            executed_at=blueprint.executed_at.isoformat() if blueprint.executed_at else None,
        )
        
    except Exception as e:
        logger.error(f"Error drafting playbook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate playbook: {str(e)}")


@router.post("/ai-playbooks/{blueprint_id}/execute", response_model=Dict[str, Any])
def execute_ai_playbook(
    blueprint_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Execute a playbook blueprint: create segment, campaign, etc.
    """
    blueprint = db.query(AIPlaybookBlueprintORM).filter(
        AIPlaybookBlueprintORM.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    if blueprint.status != PlaybookBlueprintStatus.draft:
        raise HTTPException(status_code=400, detail=f"Blueprint already {blueprint.status.value}")
    
    try:
        results = execute_playbook_blueprint(
            db=db,
            blueprint=blueprint,
            workspace_id=blueprint.workspace_id,
            organization_id=blueprint.organization_id,
            created_by_user_id=current_user_id,
        )
        
        return {
            "blueprint_id": blueprint.id,
            "status": blueprint.status.value,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"Error executing playbook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute playbook: {str(e)}")


@router.get("/ai-playbooks/{blueprint_id}", response_model=BlueprintOut)
def get_ai_playbook(
    blueprint_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get a playbook blueprint
    """
    blueprint = db.query(AIPlaybookBlueprintORM).filter(
        AIPlaybookBlueprintORM.id == blueprint_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    return BlueprintOut(
        id=blueprint.id,
        name=blueprint.name,
        description=blueprint.description,
        user_prompt=blueprint.user_prompt,
        blueprint_json=blueprint.blueprint_json,
        status=blueprint.status.value,
        segment_id=blueprint.segment_id,
        playbook_id=blueprint.playbook_id,
        campaign_id=blueprint.campaign_id,
        list_id=blueprint.list_id,
        created_at=blueprint.created_at.isoformat(),
        executed_at=blueprint.executed_at.isoformat() if blueprint.executed_at else None,
    )


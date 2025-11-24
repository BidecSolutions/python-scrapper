"""Email sync API routes"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.core.db import get_db
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.core.orm_email_sync import EmailSyncConfigORM, EmailMessageORM
from app.services.email_sync_service import process_inbound_email

logger = logging.getLogger(__name__)
router = APIRouter()


class EmailSyncConfigOut(BaseModel):
    id: int
    workspace_id: int
    bcc_email: Optional[str]
    sync_type: str
    enabled: bool
    last_sync_at: Optional[str]
    
    class Config:
        from_attributes = True


class ProcessEmailRequest(BaseModel):
    raw_email: str = Field(..., description="Raw email content (RFC 2822 format)")
    workspace_id: Optional[int] = Field(None, description="Workspace ID (if not in context)")


@router.get("/email-sync/config", response_model=EmailSyncConfigOut)
def get_email_sync_config(
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get email sync configuration for workspace
    """
    org = get_or_create_default_org(db)
    
    # TODO: Get workspace from context or parameter
    if not workspace_id:
        # For now, use first workspace or create default
        from app.core.orm_workspaces import WorkspaceORM
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.organization_id == org.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="No workspace found")
        workspace_id = workspace.id
    
    config = db.query(EmailSyncConfigORM).filter(
        EmailSyncConfigORM.workspace_id == workspace_id
    ).first()
    
    if not config:
        # Create default config
        config = EmailSyncConfigORM(
            workspace_id=workspace_id,
            organization_id=org.id,
            bcc_email=f"reply+{workspace_id}@bidec.ai",  # TODO: Use actual domain
            sync_type="bcc",
            enabled=True,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return EmailSyncConfigOut(
        id=config.id,
        workspace_id=config.workspace_id,
        bcc_email=config.bcc_email,
        sync_type=config.sync_type,
        enabled=config.enabled,
        last_sync_at=config.last_sync_at.isoformat() if config.last_sync_at else None,
    )


@router.post("/email-sync/process", response_model=dict)
def process_email(
    request: ProcessEmailRequest = Body(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Process an inbound email (webhook endpoint for email sync)
    
    This endpoint can be called by:
    - IMAP polling service
    - Gmail/Outlook webhook
    - Manual email submission
    """
    org = get_or_create_default_org(db)
    
    # Get workspace
    workspace_id = request.workspace_id
    if not workspace_id:
        from app.core.orm_workspaces import WorkspaceORM
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.organization_id == org.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="No workspace found")
        workspace_id = workspace.id
    
    try:
        email_msg = process_inbound_email(
            db=db,
            raw_email=request.raw_email,
            workspace_id=workspace_id,
            organization_id=org.id,
        )
        
        return {
            "id": email_msg.id,
            "processed": email_msg.processed,
            "is_bounce": email_msg.is_bounce,
            "is_reply": email_msg.is_reply,
            "is_unsubscribe": email_msg.is_unsubscribe,
            "is_ooo": email_msg.is_ooo,
            "campaign_id": email_msg.campaign_id,
            "lead_id": email_msg.lead_id,
        }
    except Exception as e:
        logger.error(f"Error processing email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process email: {str(e)}")


@router.get("/email-sync/messages")
def list_email_messages(
    workspace_id: Optional[int] = None,
    campaign_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    List email messages (for debugging and UI)
    """
    org = get_or_create_default_org(db)
    
    if not workspace_id:
        from app.core.orm_workspaces import WorkspaceORM
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.organization_id == org.id
        ).first()
        if workspace:
            workspace_id = workspace.id
    
    query = db.query(EmailMessageORM).filter(
        EmailMessageORM.organization_id == org.id
    )
    
    if workspace_id:
        query = query.filter(EmailMessageORM.workspace_id == workspace_id)
    
    if campaign_id:
        query = query.filter(EmailMessageORM.campaign_id == campaign_id)
    
    if lead_id:
        query = query.filter(EmailMessageORM.lead_id == lead_id)
    
    messages = query.order_by(EmailMessageORM.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": m.id,
            "direction": m.direction.value,
            "subject": m.subject,
            "from_email": m.from_email,
            "to_email": m.to_email,
            "is_bounce": m.is_bounce,
            "is_reply": m.is_reply,
            "is_unsubscribe": m.is_unsubscribe,
            "is_ooo": m.is_ooo,
            "campaign_id": m.campaign_id,
            "lead_id": m.lead_id,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


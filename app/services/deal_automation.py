"""Deal automation service - auto-create deals from positive replies"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.orm_deals import DealORM, DealStage
from app.core.orm import LeadORM
from app.services.activity_logger import log_activity, ActivityType
from app.services.notification_service import create_notification, NotificationType
from app.core.orm_tasks_notes import LeadTaskORM, TaskType, TaskStatus

logger = logging.getLogger(__name__)


def create_deal_from_positive_reply(
    db: Session,
    *,
    lead: LeadORM,
    campaign_id: Optional[int] = None,
    segment_id: Optional[int] = None,
    reply_text: Optional[str] = None,
) -> Optional[DealORM]:
    """
    Create a deal from a positive reply, or update existing deal stage.
    
    Returns the deal (new or updated), or None if no deal should be created.
    """
    if not lead.workspace_id:
        logger.warning(f"Lead {lead.id} has no workspace_id, cannot create deal")
        return None
    
    # Check if lead already has an open deal (not won/lost)
    existing_deal = db.query(DealORM).filter(
        DealORM.primary_lead_id == lead.id,
        DealORM.workspace_id == lead.workspace_id,
        ~DealORM.stage.in_([DealStage.won, DealStage.lost])
    ).first()
    
    if existing_deal:
        # Update existing deal stage to qualified or contacted
        if existing_deal.stage == DealStage.new:
            existing_deal.stage = DealStage.contacted
        elif existing_deal.stage == DealStage.contacted:
            existing_deal.stage = DealStage.qualified
        existing_deal.updated_at = datetime.utcnow()
        db.add(existing_deal)
        db.commit()
        db.refresh(existing_deal)
        
        logger.info(f"Updated existing deal {existing_deal.id} to stage {existing_deal.stage.value} from positive reply")
        return existing_deal
    
    # Create new deal
    deal_name = f"{lead.name or lead.email} – Opportunity"
    if lead.company_name:
        deal_name = f"{lead.company_name} – Opportunity"
    
    deal = DealORM(
        workspace_id=lead.workspace_id,
        organization_id=lead.organization_id,
        name=deal_name,
        company_id=lead.company_id,
        primary_lead_id=lead.id,
        owner_user_id=lead.owner_user_id or lead.assigned_to_user_id,
        stage=DealStage.qualified,  # Positive reply = qualified
        source_campaign_id=campaign_id,
        source_segment_id=segment_id,
        expected_close_date=datetime.utcnow() + timedelta(days=30),  # Default 30 days
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    
    # Log activity
    log_activity(
        db,
        organization_id=lead.organization_id,
        workspace_id=lead.workspace_id,
        type=ActivityType.deal_created,
        actor_user_id=None,  # System event
        lead_id=lead.id,
        deal_id=deal.id,
        meta={
            "deal_name": deal.name,
            "stage": deal.stage.value,
            "source": "positive_reply",
            "reply_snippet": reply_text[:100] if reply_text else None,
        }
    )
    
    # Create follow-up task for deal owner
    if deal.owner_user_id:
        task = LeadTaskORM(
            workspace_id=lead.workspace_id,
            organization_id=lead.organization_id,
            lead_id=lead.id,
            user_id=deal.owner_user_id,
            assigned_to_user_id=deal.owner_user_id,
            title="Schedule discovery call",
            type=TaskType.call,
            status=TaskStatus.open,
            due_at=datetime.utcnow() + timedelta(days=3),  # Due in 3 days
            description="Follow up on positive reply - schedule discovery call",
        )
        db.add(task)
        db.commit()
    
    # Create notification
    if deal.owner_user_id:
        create_notification(
            db,
            workspace_id=lead.workspace_id,
            user_id=deal.owner_user_id,
            type=NotificationType.reply_received,
            title="New opportunity created",
            body=f"Deal created from positive reply: {deal.name}",
            target_url=f"/deals/{deal.id}",
            meta={"deal_id": deal.id, "lead_id": lead.id},
        )
    
    logger.info(f"Created deal {deal.id} from positive reply for lead {lead.id}")
    return deal


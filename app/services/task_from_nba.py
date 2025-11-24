"""Helper to create tasks from Next Best Action"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.orm import LeadORM
from app.core.orm_tasks_notes import LeadTaskORM, TaskType, TaskStatus
from app.services.next_best_action_service import NextActionType
from app.services.activity_logger import log_activity, ActivityType

logger = logging.getLogger(__name__)


def ensure_task_from_next_action(
    db: Session,
    lead: LeadORM,
    user_id: int,
) -> Optional[LeadTaskORM]:
    """
    Create a task based on lead's next best action
    
    Returns the created task, or None if no task should be created
    """
    if not lead.next_action:
        return None
    
    # Check if a similar task already exists
    existing_task = db.query(LeadTaskORM).filter(
        LeadTaskORM.lead_id == lead.id,
        LeadTaskORM.status == TaskStatus.open,
        LeadTaskORM.type.in_([
            TaskType.follow_up,
            TaskType.enrich,
            TaskType.add_to_campaign,
        ])
    ).first()
    
    if existing_task:
        # Don't create duplicate
        return None
    
    task = None
    
    if lead.next_action == NextActionType.schedule_follow_up.value:
        # Create follow-up task
        task = LeadTaskORM(
            organization_id=lead.organization_id,
            workspace_id=lead.workspace_id,
            lead_id=lead.id,
            user_id=user_id,
            assigned_to_user_id=user_id,
            title="Follow up after reply",
            type=TaskType.follow_up,
            status=TaskStatus.open,
            due_at=datetime.utcnow() + timedelta(days=2),  # Due in 2 days
            description=lead.next_action_reason,
        )
        db.add(task)
        db.flush()
        
        # Log activity
        log_activity(
            db=db,
            organization_id=lead.organization_id,
            workspace_id=lead.workspace_id,
            type=ActivityType.task_created,
            actor_user_id=user_id,
            lead_id=lead.id,
            task_id=task.id,
            meta={"title": task.title, "type": task.type.value, "from_nba": True},
        )
        
    elif lead.next_action == NextActionType.review_or_enrich.value:
        # Create enrich task
        task = LeadTaskORM(
            organization_id=lead.organization_id,
            workspace_id=lead.workspace_id,
            lead_id=lead.id,
            user_id=user_id,
            assigned_to_user_id=user_id,
            title="Enrich lead",
            type=TaskType.enrich,
            status=TaskStatus.open,
            description=lead.next_action_reason,
        )
        db.add(task)
        db.flush()
        
        # Log activity
        log_activity(
            db=db,
            organization_id=lead.organization_id,
            workspace_id=lead.workspace_id,
            type=ActivityType.task_created,
            actor_user_id=user_id,
            lead_id=lead.id,
            task_id=task.id,
            meta={"title": task.title, "type": task.type.value, "from_nba": True},
        )
        
    elif lead.next_action == NextActionType.add_to_campaign.value:
        # Create add to campaign task
        task = LeadTaskORM(
            organization_id=lead.organization_id,
            workspace_id=lead.workspace_id,
            lead_id=lead.id,
            user_id=user_id,
            assigned_to_user_id=user_id,
            title="Add to campaign",
            type=TaskType.add_to_campaign,
            status=TaskStatus.open,
            description=lead.next_action_reason,
        )
        db.add(task)
        db.flush()
        
        # Log activity
        log_activity(
            db=db,
            organization_id=lead.organization_id,
            workspace_id=lead.workspace_id,
            type=ActivityType.task_created,
            actor_user_id=user_id,
            lead_id=lead.id,
            task_id=task.id,
            meta={"title": task.title, "type": task.type.value, "from_nba": True},
        )
    
    if task:
        db.commit()
        db.refresh(task)
        logger.info(f"Created task from NBA for lead {lead.id}: {task.title}")
    
    return task


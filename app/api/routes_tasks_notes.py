"""Tasks and Notes API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm import LeadORM, OrganizationORM
from app.core.orm_tasks_notes import LeadNoteORM, LeadTaskORM, TaskStatus, TaskType
from app.core.orm_workspaces import WorkspaceORM
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.services.activity_logger import log_activity, ActivityType
from app.services.task_from_nba import ensure_task_from_next_action

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Notes
# ============================================================================

class NoteCreate(BaseModel):
    """Request to create a note"""
    content: str = Field(..., min_length=1, max_length=2000, description="Note content")


class NoteOut(BaseModel):
    """Note response"""
    id: int
    content: str
    user_id: int
    user_name: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("/leads/{lead_id}/notes", response_model=List[NoteOut])
def get_lead_notes(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get all notes for a lead (most recent first)"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    notes = db.query(LeadNoteORM).filter(
        LeadNoteORM.lead_id == lead_id,
        LeadNoteORM.organization_id == org.id
    ).order_by(LeadNoteORM.created_at.desc()).all()
    
    result = []
    for note in notes:
        user_name = None
        if note.user:
            user_name = note.user.full_name or note.user.email
        
        result.append(NoteOut(
            id=note.id,
            content=note.content,
            user_id=note.user_id,
            user_name=user_name,
            created_at=note.created_at.isoformat(),
            updated_at=note.updated_at.isoformat(),
        ))
    
    return result


@router.post("/leads/{lead_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_lead_note(
    lead_id: int,
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Create a note for a lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Create note
    note = LeadNoteORM(
        organization_id=org.id,
        workspace_id=lead.workspace_id,
        lead_id=lead_id,
        user_id=current_user_id,
        content=note_data.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    # Log activity
    log_activity(
        db=db,
        organization_id=org.id,
        workspace_id=lead.workspace_id,
        type=ActivityType.note_added,
        actor_user_id=current_user_id,
        lead_id=lead_id,
        note_id=note.id,
        meta={"content_preview": note_data.content[:100]},
    )
    
    user_name = None
    if note.user:
        user_name = note.user.full_name or note.user.email
    
    return NoteOut(
        id=note.id,
        content=note.content,
        user_id=note.user_id,
        user_name=user_name,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


# ============================================================================
# Tasks
# ============================================================================

class TaskCreate(BaseModel):
    """Request to create a task"""
    title: str = Field(..., min_length=1, max_length=255)
    type: TaskType = Field(default=TaskType.custom)
    due_at: Optional[str] = Field(None, description="Due date in ISO format")
    description: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Request to update a task"""
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[str] = None
    description: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class TaskOut(BaseModel):
    """Task response"""
    id: int
    title: str
    type: str
    status: str
    due_at: Optional[str] = None
    completed_at: Optional[str] = None
    description: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    lead_id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("/leads/{lead_id}/tasks", response_model=List[TaskOut])
def get_lead_tasks(
    lead_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status: open, done, all"),
    db: Session = Depends(get_db),
):
    """Get all tasks for a lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    query = db.query(LeadTaskORM).filter(
        LeadTaskORM.lead_id == lead_id,
        LeadTaskORM.organization_id == org.id
    )
    
    if status_filter and status_filter != "all":
        query = query.filter(LeadTaskORM.status == status_filter)
    
    tasks = query.order_by(
        LeadTaskORM.status.asc(),  # Open tasks first
        LeadTaskORM.due_at.asc().nullslast(),  # Then by due date
        LeadTaskORM.created_at.desc()
    ).all()
    
    result = []
    for task in tasks:
        user_name = None
        if task.user:
            user_name = task.user.full_name or task.user.email
        
        assigned_to_name = None
        if task.assigned_to:
            assigned_to_name = task.assigned_to.full_name or task.assigned_to.email
        
        result.append(TaskOut(
            id=task.id,
            title=task.title,
            type=task.type.value,
            status=task.status.value,
            due_at=task.due_at.isoformat() if task.due_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            description=task.description,
            user_id=task.user_id,
            user_name=user_name,
            assigned_to_user_id=task.assigned_to_user_id,
            assigned_to_name=assigned_to_name,
            lead_id=task.lead_id,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        ))
    
    return result


@router.post("/leads/{lead_id}/tasks/from-nba", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_from_nba(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Create a task from lead's Next Best Action"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not lead.next_action:
        raise HTTPException(status_code=400, detail="Lead has no next action")
    
    # Create task from NBA
    task = ensure_task_from_next_action(db, lead, current_user_id)
    
    if not task:
        raise HTTPException(status_code=400, detail="Could not create task from next action")
    
    user_name = None
    if task.user:
        user_name = task.user.full_name or task.user.email
    
    assigned_to_name = None
    if task.assigned_to:
        assigned_to_name = task.assigned_to.full_name or task.assigned_to.email
    
    return TaskOut(
        id=task.id,
        title=task.title,
        type=task.type.value,
        status=task.status.value,
        due_at=task.due_at.isoformat() if task.due_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        description=task.description,
        user_id=task.user_id,
        user_name=user_name,
        assigned_to_user_id=task.assigned_to_user_id,
        assigned_to_name=assigned_to_name,
        lead_id=task.lead_id,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.post("/leads/{lead_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_lead_task(
    lead_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Create a task for a lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Parse due date
    due_at = None
    if task_data.due_at:
        try:
            due_at = datetime.fromisoformat(task_data.due_at.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_at format. Use ISO 8601.")
    
    # Create task
    task = LeadTaskORM(
        organization_id=org.id,
        workspace_id=lead.workspace_id,
        lead_id=lead_id,
        user_id=current_user_id,
        assigned_to_user_id=task_data.assigned_to_user_id or current_user_id,
        title=task_data.title,
        type=task_data.type,
        status=TaskStatus.open,
        due_at=due_at,
        description=task_data.description,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Log activity
    log_activity(
        db=db,
        organization_id=org.id,
        workspace_id=lead.workspace_id,
        type=ActivityType.task_created,
        actor_user_id=current_user_id,
        lead_id=lead_id,
        task_id=task.id,
        meta={"title": task.title, "type": task.type.value},
    )
    
    user_name = None
    if task.user:
        user_name = task.user.full_name or task.user.email
    
    assigned_to_name = None
    if task.assigned_to:
        assigned_to_name = task.assigned_to.full_name or task.assigned_to.email
    
    return TaskOut(
        id=task.id,
        title=task.title,
        type=task.type.value,
        status=task.status.value,
        due_at=task.due_at.isoformat() if task.due_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        description=task.description,
        user_id=task.user_id,
        user_name=user_name,
        assigned_to_user_id=task.assigned_to_user_id,
        assigned_to_name=assigned_to_name,
        lead_id=task.lead_id,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Update a task (status, title, due date, etc.)"""
    org = get_or_create_default_org(db)
    
    task = db.query(LeadTaskORM).filter(
        LeadTaskORM.id == task_id,
        LeadTaskORM.organization_id == org.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.status is not None:
        old_status = task.status
        task.status = task_data.status
        
        # Set completed_at if marking as done
        if task_data.status == TaskStatus.done and not task.completed_at:
            task.completed_at = datetime.utcnow()
            # Log completion
            log_activity(
                db=db,
                organization_id=org.id,
                workspace_id=task.workspace_id,
                type=ActivityType.task_completed,
                actor_user_id=current_user_id,
                lead_id=task.lead_id,
                task_id=task.id,
                meta={"title": task.title},
            )
        elif task_data.status != TaskStatus.done:
            task.completed_at = None
    
    if task_data.due_at is not None:
        if task_data.due_at:
            try:
                task.due_at = datetime.fromisoformat(task_data.due_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_at format")
        else:
            task.due_at = None
    
    if task_data.description is not None:
        task.description = task_data.description
    
    if task_data.assigned_to_user_id is not None:
        task.assigned_to_user_id = task_data.assigned_to_user_id
    
    db.commit()
    db.refresh(task)
    
    user_name = None
    if task.user:
        user_name = task.user.full_name or task.user.email
    
    assigned_to_name = None
    if task.assigned_to:
        assigned_to_name = task.assigned_to.full_name or task.assigned_to.email
    
    return TaskOut(
        id=task.id,
        title=task.title,
        type=task.type.value,
        status=task.status.value,
        due_at=task.due_at.isoformat() if task.due_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        description=task.description,
        user_id=task.user_id,
        user_name=user_name,
        assigned_to_user_id=task.assigned_to_user_id,
        assigned_to_name=assigned_to_name,
        lead_id=task.lead_id,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.get("/tasks", response_model=List[TaskOut])
def get_tasks(
    workspace_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, description="open, done, all"),
    assigned_to_user_id: Optional[int] = Query(None),
    due_filter: Optional[str] = Query(None, description="overdue, today, this_week"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Get all tasks (workspace-scoped)"""
    org = get_or_create_default_org(db)
    
    query = db.query(LeadTaskORM).filter(
        LeadTaskORM.organization_id == org.id
    )
    
    if workspace_id:
        query = query.filter(LeadTaskORM.workspace_id == workspace_id)
    
    if status_filter and status_filter != "all":
        query = query.filter(LeadTaskORM.status == status_filter)
    
    if assigned_to_user_id:
        query = query.filter(LeadTaskORM.assigned_to_user_id == assigned_to_user_id)
    else:
        # Default to current user's tasks if no filter
        query = query.filter(LeadTaskORM.assigned_to_user_id == current_user_id)
    
    if due_filter:
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        if due_filter == "overdue":
            query = query.filter(
                LeadTaskORM.due_at < now,
                LeadTaskORM.status == TaskStatus.open
            )
        elif due_filter == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.filter(
                LeadTaskORM.due_at >= start_of_day,
                LeadTaskORM.due_at < end_of_day,
                LeadTaskORM.status == TaskStatus.open
            )
        elif due_filter == "this_week":
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_week = start_of_week + timedelta(days=7)
            query = query.filter(
                LeadTaskORM.due_at >= start_of_week,
                LeadTaskORM.due_at < end_of_week,
                LeadTaskORM.status == TaskStatus.open
            )
    
    tasks = query.order_by(
        LeadTaskORM.due_at.asc().nullslast(),
        LeadTaskORM.created_at.desc()
    ).all()
    
    result = []
    for task in tasks:
        user_name = None
        if task.user:
            user_name = task.user.full_name or task.user.email
        
        assigned_to_name = None
        if task.assigned_to:
            assigned_to_name = task.assigned_to.full_name or task.assigned_to.email
        
        result.append(TaskOut(
            id=task.id,
            title=task.title,
            type=task.type.value,
            status=task.status.value,
            due_at=task.due_at.isoformat() if task.due_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            description=task.description,
            user_id=task.user_id,
            user_name=user_name,
            assigned_to_user_id=task.assigned_to_user_id,
            assigned_to_name=assigned_to_name,
            lead_id=task.lead_id,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        ))
    
    return result


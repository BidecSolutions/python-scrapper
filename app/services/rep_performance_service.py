"""Rep Performance & Leaderboard service"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case

from app.core.orm import UserORM, LeadORM, OrganizationORM
from app.core.orm_tasks_notes import LeadTaskORM, TaskStatus
from app.core.orm_activity import ActivityORM, ActivityType
from app.core.orm_workspaces import WorkspaceMemberORM, WorkspaceORM

logger = logging.getLogger(__name__)


@dataclass
class RepPerformance:
    """Rep performance metrics"""
    user_id: int
    name: str
    email: str
    role: Optional[str] = None
    
    # Lead metrics
    new_leads_owned: int = 0
    leads_worked: int = 0
    
    # Task metrics
    tasks_created: int = 0
    tasks_completed: int = 0
    task_completion_rate: float = 0.0
    
    # Campaign metrics
    campaign_leads_sent: int = 0
    campaign_opens: int = 0
    campaign_replies: int = 0
    campaign_bounces: int = 0
    campaign_reply_rate: float = 0.0
    campaign_open_rate: float = 0.0
    campaign_bounce_rate: float = 0.0
    
    # Source breakdown
    source_breakdown: Dict[str, float] = None  # {source: percentage}
    
    def __post_init__(self):
        if self.source_breakdown is None:
            self.source_breakdown = {}


def get_rep_performance(
    db: Session,
    organization_id: int,
    workspace_id: Optional[int] = None,
    *,
    days: int = 30,
    user_id: Optional[int] = None,  # If provided, only get this user's stats
) -> List[RepPerformance]:
    """
    Get rep performance metrics for workspace members
    
    Args:
        db: Database session
        organization_id: Organization ID
        workspace_id: Optional workspace ID
        days: Number of days to look back
        user_id: Optional specific user ID (for per-rep view)
    
    Returns:
        List of RepPerformance objects
    """
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    
    # Get workspace members
    if workspace_id:
        members_query = db.query(WorkspaceMemberORM).filter(
            WorkspaceMemberORM.workspace_id == workspace_id,
            WorkspaceMemberORM.accepted_at.isnot(None)
        )
        if user_id:
            members_query = members_query.filter(WorkspaceMemberORM.user_id == user_id)
        
        members = members_query.all()
        user_ids = [m.user_id for m in members if m.user_id]
    else:
        # Get all users in organization
        users_query = db.query(UserORM).filter(UserORM.organization_id == organization_id)
        if user_id:
            users_query = users_query.filter(UserORM.id == user_id)
        users = users_query.all()
        user_ids = [u.id for u in users]
    
    if not user_ids:
        return []
    
    # Get users with their workspace roles
    users = db.query(UserORM).filter(UserORM.id.in_(user_ids)).all()
    user_roles = {}
    if workspace_id:
        for member in members:
            if member.user_id:
                user_roles[member.user_id] = member.role.value if member.role else None
    
    results = []
    
    for user in users:
        user_id = user.id
        
        # 1. New leads owned (use owner_user_id, fallback to created_by_user_id)
        new_leads_owned = db.query(func.count(LeadORM.id)).filter(
            LeadORM.organization_id == organization_id,
            or_(
                LeadORM.owner_user_id == user_id,
                and_(
                    LeadORM.owner_user_id.is_(None),
                    LeadORM.created_by_user_id == user_id
                )
            ),
            LeadORM.created_at >= since
        ).scalar() or 0
        
        # 2. Leads worked (distinct leads with tasks or notes by this user)
        # Leads with tasks
        leads_with_tasks = db.query(LeadORM.id).join(
            LeadTaskORM, LeadTaskORM.lead_id == LeadORM.id
        ).filter(
            LeadORM.organization_id == organization_id,
            LeadTaskORM.user_id == user_id,
            LeadTaskORM.created_at >= since
        ).distinct()
        
        # Leads with notes
        from app.core.orm_tasks_notes import LeadNoteORM
        leads_with_notes = db.query(LeadORM.id).join(
            LeadNoteORM, LeadNoteORM.lead_id == LeadORM.id
        ).filter(
            LeadORM.organization_id == organization_id,
            LeadNoteORM.user_id == user_id,
            LeadNoteORM.created_at >= since
        ).distinct()
        
        # Combine and count distinct
        all_worked_lead_ids = set()
        for row in leads_with_tasks.all():
            all_worked_lead_ids.add(row[0])
        for row in leads_with_notes.all():
            all_worked_lead_ids.add(row[0])
        
        leads_worked = len(all_worked_lead_ids)
        
        # 3. Tasks created and completed
        tasks_created = db.query(func.count(LeadTaskORM.id)).filter(
            LeadTaskORM.organization_id == organization_id,
            LeadTaskORM.user_id == user_id,
            LeadTaskORM.created_at >= since
        ).scalar() or 0
        
        tasks_completed = db.query(func.count(LeadTaskORM.id)).filter(
            LeadTaskORM.organization_id == organization_id,
            LeadTaskORM.user_id == user_id,
            LeadTaskORM.status == TaskStatus.done,
            LeadTaskORM.completed_at >= since
        ).scalar() or 0
        
        task_completion_rate = (tasks_completed / tasks_created * 100) if tasks_created > 0 else 0.0
        
        # 4. Campaign impact (on leads owned by this user)
        # Check if campaign models exist
        campaign_leads_sent = 0
        campaign_opens = 0
        campaign_replies = 0
        campaign_bounces = 0
        
        try:
            from app.core.orm import CampaignORM, CampaignLeadORM
            
            # Get leads owned by this user (use owner_user_id, fallback to created_by_user_id)
            owned_lead_ids = db.query(LeadORM.id).filter(
                LeadORM.organization_id == organization_id,
                or_(
                    LeadORM.owner_user_id == user_id,
                    and_(
                        LeadORM.owner_user_id.is_(None),
                        LeadORM.created_by_user_id == user_id
                    )
                )
            ).subquery()
            
            # Campaign stats
            stats = db.query(
                func.count(func.distinct(CampaignLeadORM.lead_id)).label("sent"),
                func.sum(case((CampaignLeadORM.opened == True, 1), else_=0)).label("opened"),
                func.sum(case((CampaignLeadORM.replied == True, 1), else_=0)).label("replied"),
                func.sum(case((CampaignLeadORM.bounced == True, 1), else_=0)).label("bounced"),
            ).join(
                CampaignORM, CampaignORM.id == CampaignLeadORM.campaign_id
            ).filter(
                CampaignLeadORM.lead_id.in_(db.query(owned_lead_ids.c.id)),
                CampaignORM.organization_id == organization_id,
                CampaignORM.sent_at >= since,
            ).first()
            
            if stats:
                campaign_leads_sent = stats.sent or 0
                campaign_opens = stats.opened or 0
                campaign_replies = stats.replied or 0
                campaign_bounces = stats.bounced or 0
        except (ImportError, AttributeError):
            # Campaign models don't exist, use activity logs or metadata
            # This is a simplified fallback
            pass
        
        # Calculate rates
        campaign_reply_rate = (campaign_replies / campaign_leads_sent * 100) if campaign_leads_sent > 0 else 0.0
        campaign_open_rate = (campaign_opens / campaign_leads_sent * 100) if campaign_leads_sent > 0 else 0.0
        campaign_bounce_rate = (campaign_bounces / campaign_leads_sent * 100) if campaign_leads_sent > 0 else 0.0
        
        # 5. Source breakdown (for leads owned by this user in time window)
        source_counts = db.query(
            LeadORM.source,
            func.count(LeadORM.id).label("count")
        ).filter(
            LeadORM.organization_id == organization_id,
            or_(
                LeadORM.owner_user_id == user_id,
                and_(
                    LeadORM.owner_user_id.is_(None),
                    LeadORM.created_by_user_id == user_id
                )
            ),
            LeadORM.created_at >= since,
            LeadORM.source.isnot(None)
        ).group_by(LeadORM.source).all()
        
        total_leads_with_source = sum(count for _, count in source_counts)
        source_breakdown = {}
        if total_leads_with_source > 0:
            for source, count in source_counts:
                source_breakdown[source or "unknown"] = (count / total_leads_with_source) * 100
        
        # Build result
        perf = RepPerformance(
            user_id=user.id,
            name=user.full_name or user.email or f"User {user.id}",
            email=user.email or "",
            role=user_roles.get(user_id),
            new_leads_owned=new_leads_owned,
            leads_worked=leads_worked,
            tasks_created=tasks_created,
            tasks_completed=tasks_completed,
            task_completion_rate=round(task_completion_rate, 2),
            campaign_leads_sent=campaign_leads_sent,
            campaign_opens=campaign_opens,
            campaign_replies=campaign_replies,
            campaign_bounces=campaign_bounces,
            campaign_reply_rate=round(campaign_reply_rate, 2),
            campaign_open_rate=round(campaign_open_rate, 2),
            campaign_bounce_rate=round(campaign_bounce_rate, 2),
            source_breakdown=source_breakdown,
        )
        
        results.append(perf)
    
    return results


def get_rep_leaderboard(
    db: Session,
    organization_id: int,
    workspace_id: Optional[int] = None,
    *,
    days: int = 30,
    sort_by: str = "replies",  # "replies", "leads_worked", "tasks_completed"
) -> List[RepPerformance]:
    """
    Get rep leaderboard sorted by specified metric
    
    Args:
        db: Database session
        organization_id: Organization ID
        workspace_id: Optional workspace ID
        days: Number of days to look back
        sort_by: Sort metric ("replies", "leads_worked", "tasks_completed")
    
    Returns:
        Sorted list of RepPerformance objects
    """
    results = get_rep_performance(
        db=db,
        organization_id=organization_id,
        workspace_id=workspace_id,
        days=days,
    )
    
    # Sort by metric
    if sort_by == "replies":
        results.sort(key=lambda r: r.campaign_replies, reverse=True)
    elif sort_by == "leads_worked":
        results.sort(key=lambda r: r.leads_worked, reverse=True)
    elif sort_by == "tasks_completed":
        results.sort(key=lambda r: r.tasks_completed, reverse=True)
    elif sort_by == "reply_rate":
        results.sort(key=lambda r: r.campaign_reply_rate, reverse=True)
    else:
        # Default to replies
        results.sort(key=lambda r: r.campaign_replies, reverse=True)
    
    return results


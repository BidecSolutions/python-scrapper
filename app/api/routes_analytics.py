"""Analytics tracking API routes"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.core.orm import OrganizationORM
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyticsEvent(BaseModel):
    """Analytics event schema"""
    event_type: str  # e.g., "extension_capture", "extension_find_email", "extension_save_to_list"
    properties: dict = {}  # Additional event properties
    timestamp: Optional[datetime] = None


@router.post("/analytics/events")
def track_event(
    event: AnalyticsEvent,
    db: Session = Depends(get_db),
):
    """
    Track an analytics event
    
    For now, this just logs the event. In the future, you can:
    - Store in a dedicated analytics table
    - Send to external analytics service (Mixpanel, Amplitude, etc.)
    - Aggregate for dashboard metrics
    """
    org = get_or_create_default_org(db)
    
    # Log the event
    logger.info(f"Analytics event: {event.event_type} for org {org.id}", extra={
        "organization_id": org.id,
        "event_type": event.event_type,
        "properties": event.properties,
        "timestamp": event.timestamp or datetime.utcnow(),
    })
    
    # TODO: Store in analytics table or send to external service
    # For now, we'll just log it
    
    return {
        "success": True,
        "event_type": event.event_type,
        "logged_at": datetime.utcnow().isoformat(),
    }


@router.get("/analytics/extension-usage")
def get_extension_usage(
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Get extension usage statistics
    
    Returns aggregated stats for extension events
    """
    org = get_or_create_default_org(db)
    
    # For now, return basic stats based on leads
    # In the future, query from analytics table
    from datetime import timedelta
    from sqlalchemy import func
    from app.core.orm import LeadORM
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    total_captures = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org.id,
        LeadORM.source == "linkedin_extension",
        LeadORM.created_at >= cutoff
    ).scalar() or 0
    
    # Get daily breakdown (last 7 days)
    from datetime import date
    daily_stats = []
    for i in range(7):
        day_start = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = db.query(func.count(LeadORM.id)).filter(
            LeadORM.organization_id == org.id,
            LeadORM.source == "linkedin_extension",
            LeadORM.created_at >= day_start,
            LeadORM.created_at < day_end
        ).scalar() or 0
        
        daily_stats.append({
            "date": day_start.date().isoformat(),
            "count": count,
        })
    
    daily_stats.reverse()  # Oldest first
    
    return {
        "total_captures": total_captures,
        "period_days": days,
        "daily_breakdown": daily_stats,
    }


"""Dashboard segments performance API routes"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.schemas.dashboard_segments import TopSegmentsResponse
from app.services.dashboard_segments_service import get_top_segments

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard/top-segments", response_model=TopSegmentsResponse)
def top_segments(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    metric: str = Query("reply_rate", description="Sort metric: 'reply_rate' or 'open_rate'"),
    limit: int = Query(5, ge=1, le=50, description="Maximum number of segments to return"),
    workspace_id: Optional[int] = Query(None, description="Workspace ID (optional)"),
    db: Session = Depends(get_db),
):
    """
    Get top performing segments based on campaign outcomes
    
    Returns segments sorted by reply rate or open rate, showing:
    - Leads sent
    - Open rate
    - Reply rate
    - Bounce rate
    """
    org = get_or_create_default_org(db)
    
    # TODO: Get workspace_id from JWT/session if not provided
    # For now, workspace_id is optional
    
    result = get_top_segments(
        db=db,
        organization_id=org.id,
        workspace_id=workspace_id,
        days=days,
        metric=metric,
        limit=limit,
    )
    
    return result


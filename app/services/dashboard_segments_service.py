"""Dashboard segments performance service"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

from app.core.orm_segments import SegmentORM
from app.core.orm import LeadORM
from app.services.segments_service import apply_segment_filter
from app.schemas.dashboard_segments import SegmentPerformance, TopSegmentsResponse

logger = logging.getLogger(__name__)


def get_top_segments(
    db: Session,
    organization_id: int,
    workspace_id: Optional[int] = None,
    *,
    days: int = 30,
    metric: str = "reply_rate",
    limit: int = 5,
) -> TopSegmentsResponse:
    """
    Get top performing segments based on campaign outcomes
    
    Args:
        db: Database session
        organization_id: Organization ID
        workspace_id: Optional workspace ID (for workspace-scoped segments)
        days: Number of days to look back
        metric: Sort metric ("reply_rate" or "open_rate")
        limit: Maximum number of segments to return
    
    Returns:
        TopSegmentsResponse with performance data
    """
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    
    # Get all segments for the organization/workspace
    segments_query = db.query(SegmentORM).filter(
        SegmentORM.organization_id == organization_id
    )
    
    if workspace_id:
        segments_query = segments_query.filter(SegmentORM.workspace_id == workspace_id)
    
    segments = segments_query.all()
    
    if not segments:
        return TopSegmentsResponse(
            time_range_from=since,
            time_range_to=now,
            metric=metric,
            segments=[],
        )
    
    results: List[SegmentPerformance] = []
    
    # For now, we'll use a simplified approach since Campaign/CampaignLead models
    # may not exist yet. We'll track this via LeadORM metadata or create placeholder logic.
    
    # Check if we have campaign tracking data
    # This is a placeholder - adjust based on your actual campaign tracking implementation
    has_campaign_tracking = False
    
    # Try to detect if campaign models exist
    try:
        from app.core.orm import CampaignORM, CampaignLeadORM
        has_campaign_tracking = True
    except ImportError:
        logger.warning("Campaign models not found. Using simplified segment performance calculation.")
        has_campaign_tracking = False
    
    for seg in segments:
        try:
            # Build base leads query for this segment
            leads_query = db.query(LeadORM.id).filter(
                LeadORM.organization_id == organization_id
            )
            
            if workspace_id:
                leads_query = leads_query.filter(LeadORM.workspace_id == workspace_id)
            
            # Apply segment filters
            leads_query = apply_segment_filter(leads_query, seg.filter_json, organization_id)
            
            # Get lead IDs that match this segment
            matching_lead_ids = [row[0] for row in leads_query.all()]
            
            if not matching_lead_ids:
                continue  # Skip segments with no matching leads
            
            # Calculate campaign stats if campaign tracking exists
            if has_campaign_tracking:
                from app.core.orm import CampaignORM, CampaignLeadORM
                
                # Get campaign stats for these leads
                stats = db.query(
                    func.count(func.distinct(CampaignLeadORM.lead_id)).label("leads_sent"),
                    func.sum(case((CampaignLeadORM.opened == True, 1), else_=0)).label("opened"),
                    func.sum(case((CampaignLeadORM.replied == True, 1), else_=0)).label("replied"),
                    func.sum(case((CampaignLeadORM.bounced == True, 1), else_=0)).label("bounced"),
                ).join(
                    CampaignORM, CampaignORM.id == CampaignLeadORM.campaign_id
                ).filter(
                    CampaignLeadORM.lead_id.in_(matching_lead_ids),
                    CampaignORM.organization_id == organization_id,
                    CampaignORM.sent_at >= since,
                ).first()
                
                leads_sent = stats.leads_sent or 0 if stats else 0
                opened = stats.opened or 0 if stats else 0
                replied = stats.replied or 0 if stats else 0
                bounced = stats.bounced or 0 if stats else 0
            else:
                # Simplified version: use lead metadata or activity logs
                # For now, we'll use a placeholder that counts leads
                # In production, you'd track campaign outcomes in LeadORM.metadata or ActivityLogORM
                
                # Count total leads in segment
                leads_sent = len(matching_lead_ids)
                
                # Placeholder: check metadata for campaign outcomes
                # This assumes you store campaign outcomes in LeadORM.metadata
                opened = 0
                replied = 0
                bounced = 0
                
                for lead_id in matching_lead_ids:
                    lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
                    if lead and lead.metadata:
                        # Check for campaign outcomes in metadata
                        if isinstance(lead.metadata, dict):
                            if lead.metadata.get("campaign_opened"):
                                opened += 1
                            if lead.metadata.get("campaign_replied"):
                                replied += 1
                            if lead.metadata.get("campaign_bounced"):
                                bounced += 1
            
            if leads_sent == 0:
                continue  # Skip segments with no campaign activity
            
            # Calculate rates
            open_rate = (opened / leads_sent) if leads_sent > 0 else 0.0
            reply_rate = (replied / leads_sent) if leads_sent > 0 else 0.0
            bounce_rate = (bounced / leads_sent) if leads_sent > 0 else 0.0
            
            perf = SegmentPerformance(
                segment_id=seg.id,
                segment_name=seg.name,
                leads_sent=leads_sent,
                opened=opened,
                replied=replied,
                bounced=bounced,
                open_rate=round(open_rate, 4),
                reply_rate=round(reply_rate, 4),
                bounce_rate=round(bounce_rate, 4),
            )
            
            results.append(perf)
            
        except Exception as e:
            logger.error(f"Error calculating performance for segment {seg.id}: {e}", exc_info=True)
            continue
    
    # Sort by metric
    if metric == "reply_rate":
        results.sort(key=lambda p: p.reply_rate, reverse=True)
    elif metric == "open_rate":
        results.sort(key=lambda p: p.open_rate, reverse=True)
    else:
        # Default to reply_rate
        results.sort(key=lambda p: p.reply_rate, reverse=True)
    
    # Limit results
    top = results[:limit]
    
    return TopSegmentsResponse(
        time_range_from=since,
        time_range_to=now,
        metric=metric,
        segments=top,
    )


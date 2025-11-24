"""Lead Health / Priority Score calculation service"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.orm import LeadORM, EmailORM, EmailVerificationStatus
from app.core.orm_companies import CompanyORM
from app.core.orm_segments import SegmentORM
from app.services.dashboard_segments_service import get_top_segments

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    """Email verification status"""
    valid = "valid"
    risky = "risky"
    unknown = "unknown"
    invalid = "invalid"


@dataclass
class SegmentPerformanceInfo:
    """Segment performance info for scoring"""
    segment_id: int
    reply_rate: float


@dataclass
class CampaignEngagementInfo:
    """Campaign engagement stats for scoring"""
    opened_any: bool = False
    clicked_any: bool = False
    replied_any: bool = False
    bounced_any: bool = False


def get_email_status_for_lead(db: Session, lead: LeadORM) -> Optional[EmailStatus]:
    """Get email verification status for a lead"""
    email_record = db.query(EmailORM).filter(
        EmailORM.lead_id == lead.id,
        EmailORM.organization_id == lead.organization_id
    ).order_by(EmailORM.created_at.desc()).first()
    
    if not email_record:
        return None
    
    if email_record.verify_status == EmailVerificationStatus.VALID:
        return EmailStatus.valid
    elif email_record.verify_status == EmailVerificationStatus.RISKY:
        return EmailStatus.risky
    elif email_record.verify_status == EmailVerificationStatus.UNKNOWN:
        return EmailStatus.unknown
    else:
        return EmailStatus.invalid


def get_segments_for_lead(db: Session, lead: LeadORM) -> List[SegmentORM]:
    """Get all segments that match this lead"""
    # Get all segments for the organization/workspace
    segments_query = db.query(SegmentORM).filter(
        SegmentORM.organization_id == lead.organization_id
    )
    
    if lead.workspace_id:
        segments_query = segments_query.filter(SegmentORM.workspace_id == lead.workspace_id)
    
    segments = segments_query.all()
    
    matching_segments = []
    
    for segment in segments:
        # Apply segment filter to see if lead matches
        from app.services.segments_service import apply_segment_filter
        
        leads_query = db.query(LeadORM.id).filter(LeadORM.id == lead.id)
        leads_query = apply_segment_filter(leads_query, segment.filter_json, lead.organization_id)
        
        matching = leads_query.first()
        if matching:
            matching_segments.append(segment)
    
    return matching_segments


def get_segment_performance_info(
    db: Session,
    organization_id: int,
    workspace_id: Optional[int],
    segments: List[SegmentORM]
) -> List[SegmentPerformanceInfo]:
    """Get performance info for segments"""
    if not segments:
        return []
    
    # Get top segments with performance data
    top_segments_data = get_top_segments(
        db=db,
        organization_id=organization_id,
        workspace_id=workspace_id,
        days=90,  # Look back 90 days for segment performance
        metric="reply_rate",
        limit=100,  # Get all segments
    )
    
    # Create a map of segment_id -> reply_rate
    perf_map = {seg.segment_id: seg.reply_rate for seg in top_segments_data.segments}
    
    # Build performance info for matching segments
    result = []
    for segment in segments:
        reply_rate = perf_map.get(segment.id, 0.0)
        result.append(SegmentPerformanceInfo(
            segment_id=segment.id,
            reply_rate=reply_rate
        ))
    
    return result


def get_campaign_engagement_for_lead(
    db: Session,
    lead: LeadORM
) -> CampaignEngagementInfo:
    """Get campaign engagement stats for a lead"""
    # Check if campaign models exist
    try:
        from app.core.orm import CampaignORM, CampaignLeadORM
        
        # Query campaign engagement
        stats = db.query(
            func.bool_or(CampaignLeadORM.opened).label("opened_any"),
            func.bool_or(CampaignLeadORM.clicked).label("clicked_any"),
            func.bool_or(CampaignLeadORM.replied).label("replied_any"),
            func.bool_or(CampaignLeadORM.bounced).label("bounced_any"),
        ).join(
            CampaignORM, CampaignORM.id == CampaignLeadORM.campaign_id
        ).filter(
            CampaignLeadORM.lead_id == lead.id,
            CampaignORM.organization_id == lead.organization_id
        ).first()
        
        if stats:
            return CampaignEngagementInfo(
                opened_any=stats.opened_any or False,
                clicked_any=stats.clicked_any or False,
                replied_any=stats.replied_any or False,
                bounced_any=stats.bounced_any or False,
            )
    except (ImportError, AttributeError):
        # Campaign models don't exist, check lead metadata
        if lead.metadata and isinstance(lead.metadata, dict):
            return CampaignEngagementInfo(
                opened_any=lead.metadata.get("campaign_opened", False),
                clicked_any=lead.metadata.get("campaign_clicked", False),
                replied_any=lead.metadata.get("campaign_replied", False),
                bounced_any=lead.metadata.get("campaign_bounced", False),
            )
    
    return CampaignEngagementInfo()


def compute_lead_score(
    *,
    email_status: Optional[EmailStatus],
    in_segments: List[SegmentPerformanceInfo],
    title: Optional[str],
    company_size_bucket: Optional[str],
    campaigns_stats: CampaignEngagementInfo,
    source: str,
) -> float:
    """
    Compute lead health score (0-100)
    
    Components:
    - Deliverability (0-30 points)
    - Fit/ICP (0-40 points)
    - Engagement (0-20 points, with penalties)
    - Source (0-10 points)
    """
    score = 0.0
    
    # 1) Deliverability (0-30)
    if email_status == EmailStatus.valid:
        score += 30
    elif email_status == EmailStatus.risky:
        score += 15
    elif email_status == EmailStatus.unknown:
        score += 10
    # else invalid or None => +0
    
    # 2) Fit / ICP (0-40)
    fit_score = 0.0
    
    # Segments performance
    if in_segments:
        high_performing = [seg for seg in in_segments if seg.reply_rate >= 0.08]
        moderate_performing = [seg for seg in in_segments if 0.03 <= seg.reply_rate < 0.08]
        
        if high_performing:
            fit_score += 25
        elif moderate_performing:
            fit_score += 15
    
    # Title contains target roles
    if title:
        lowered = title.lower()
        targets = [
            "founder", "co-founder", "ceo", "cmo", "cfo", "cto",
            "vp marketing", "head of marketing", "director of marketing",
            "chief", "president", "owner"
        ]
        if any(t in lowered for t in targets):
            fit_score += 10
    
    # Company size in target range
    if company_size_bucket:
        # Target sizes: small to medium businesses
        target_sizes = ["2-10", "11-50", "51-200", "solo", "small", "medium"]
        if company_size_bucket.lower() in [s.lower() for s in target_sizes]:
            fit_score += 5
    
    score += min(fit_score, 40.0)
    
    # 3) Engagement (0-20, with penalties)
    if campaigns_stats.bounced_any:
        score -= 20  # Penalty for bouncing
    
    if campaigns_stats.replied_any:
        score += 20  # Max out engagement if replied
    elif campaigns_stats.clicked_any:
        score += 10
    elif campaigns_stats.opened_any:
        score += 5
    
    # 4) Source (0-10)
    source_lower = source.lower() if source else ""
    if "linkedin" in source_lower or source_lower == "linkedin_extension":
        score += 10
    elif "company_search" in source_lower or "company" in source_lower:
        score += 7
    elif "csv" in source_lower and "cleaned" in source_lower:
        score += 5
    elif "csv" in source_lower:
        score += 3
    else:
        score += 5  # Default for other sources
    
    # Clamp to 0-100
    return max(0.0, min(100.0, score))


def recompute_lead_score(db: Session, lead: LeadORM) -> float:
    """
    Recompute and save lead health score
    
    Returns the computed score
    """
    # 1) Get email status
    email_status = get_email_status_for_lead(db, lead)
    
    # 2) Get segments for lead
    segments = get_segments_for_lead(db, lead)
    
    # 3) Get segment performance
    segments_perf = get_segment_performance_info(
        db=db,
        organization_id=lead.organization_id,
        workspace_id=lead.workspace_id,
        segments=segments
    )
    
    # 4) Get campaign engagement
    campaigns_stats = get_campaign_engagement_for_lead(db, lead)
    
    # 5) Get company size
    company_size_bucket = None
    if lead.company_id:
        company = db.query(CompanyORM).filter(CompanyORM.id == lead.company_id).first()
        if company:
            company_size_bucket = company.size
    
    # 6) Compute score
    score_value = compute_lead_score(
        email_status=email_status,
        in_segments=segments_perf,
        title=lead.contact_person_role,
        company_size_bucket=company_size_bucket,
        campaigns_stats=campaigns_stats,
        source=lead.source or "",
    )
    
    # 7) Save to lead
    lead.health_score = score_value
    lead.health_score_last_calculated_at = datetime.utcnow()
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    logger.info(f"Recomputed health score for lead {lead.id}: {score_value}")
    
    return score_value


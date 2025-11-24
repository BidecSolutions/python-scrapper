"""Next Best Action (NBA) decision service"""
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.orm import LeadORM
from app.services.lead_scoring_service import get_campaign_engagement_for_lead, get_email_status_for_lead, EmailStatus

logger = logging.getLogger(__name__)


class NextActionType(str, Enum):
    """Next best action types"""
    add_to_campaign = "add_to_campaign"
    schedule_follow_up = "schedule_follow_up"
    nurture_only = "nurture_only"
    review_or_enrich = "review_or_enrich"
    drop_or_suspend = "drop_or_suspend"


# Constants
FOLLOW_UP_MIN_DAYS = 7
FOLLOW_UP_MAX_DAYS = 30
RECENCY_WINDOW_DAYS = 30


@dataclass
class LeadContext:
    """Context for NBA decision"""
    score: Optional[float]
    email_status: Optional[EmailStatus]
    has_bounced: bool
    has_replied: bool
    last_reply_at: Optional[datetime]
    last_campaign_sent_at: Optional[datetime]
    ever_in_campaign: bool
    suppressed: bool
    has_email: bool


def build_lead_context(db: Session, lead: LeadORM) -> LeadContext:
    """Build context for NBA decision from lead data"""
    # Get email status
    email_status = get_email_status_for_lead(db, lead)
    has_email = email_status is not None and email_status != EmailStatus.invalid
    
    # Get campaign engagement
    campaigns_stats = get_campaign_engagement_for_lead(db, lead)
    
    # Check if suppressed (from metadata or dedicated field)
    suppressed = False
    if lead.metadata and isinstance(lead.metadata, dict):
        suppressed = lead.metadata.get("suppressed", False) or lead.metadata.get("unsubscribed", False)
    
    # Get last reply date (from metadata or campaign data)
    last_reply_at = None
    if campaigns_stats.replied_any:
        # Try to get from metadata
        if lead.metadata and isinstance(lead.metadata, dict):
            reply_date_str = lead.metadata.get("last_reply_at")
            if reply_date_str:
                try:
                    last_reply_at = datetime.fromisoformat(reply_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
        
        # If not in metadata, use a default (e.g., 14 days ago)
        if not last_reply_at:
            last_reply_at = datetime.utcnow() - timedelta(days=14)
    
    # Get last campaign sent date
    last_campaign_sent_at = None
    if lead.metadata and isinstance(lead.metadata, dict):
        sent_date_str = lead.metadata.get("last_campaign_sent_at")
        if sent_date_str:
            try:
                last_campaign_sent_at = datetime.fromisoformat(sent_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
    
    # Check if ever in campaign
    ever_in_campaign = campaigns_stats.opened_any or campaigns_stats.replied_any or campaigns_stats.clicked_any
    
    return LeadContext(
        score=lead.health_score,
        email_status=email_status,
        has_bounced=campaigns_stats.bounced_any,
        has_replied=campaigns_stats.replied_any,
        last_reply_at=last_reply_at,
        last_campaign_sent_at=last_campaign_sent_at,
        ever_in_campaign=ever_in_campaign,
        suppressed=suppressed,
        has_email=has_email,
    )


def decide_next_action(ctx: LeadContext) -> Tuple[NextActionType, str]:
    """
    Decide next best action for a lead based on context
    
    Returns: (action_type, reason)
    """
    now = datetime.utcnow()
    
    # 1. Drop / suspend (hard stop)
    if ctx.suppressed or ctx.has_bounced:
        return (
            NextActionType.drop_or_suspend,
            "Contact is suppressed or bounced in a previous campaign.",
        )
    
    # 2. Follow-up after reply
    if ctx.has_replied and ctx.last_reply_at:
        days_since_reply = (now - ctx.last_reply_at).days
        if FOLLOW_UP_MIN_DAYS <= days_since_reply <= FOLLOW_UP_MAX_DAYS:
            return (
                NextActionType.schedule_follow_up,
                f"Replied {days_since_reply} days ago with no recent follow-up.",
            )
    
    # 3. Add to campaign (hot net new)
    if ctx.score is not None and ctx.score >= 70 and ctx.has_email:
        # Treat "no campaign" as very old
        last_sent_days = (
            (now - ctx.last_campaign_sent_at).days
            if ctx.last_campaign_sent_at
            else 9999
        )
        if not ctx.ever_in_campaign or last_sent_days > RECENCY_WINDOW_DAYS:
            return (
                NextActionType.add_to_campaign,
                f"High score ({int(ctx.score)}) and not contacted in the last {RECENCY_WINDOW_DAYS} days.",
            )
    
    # 4. Nurture
    if ctx.score is not None and 40 <= ctx.score < 70 and ctx.has_email:
        return (
            NextActionType.nurture_only,
            f"Medium score ({int(ctx.score)}); consider adding to a low-intent or nurture sequence.",
        )
    
    # 5. Review / enrich (fallback)
    if not ctx.has_email or ctx.email_status is None:
        return (
            NextActionType.review_or_enrich,
            "Missing reliable email; run Email Finder or enrichment.",
        )
    
    return (
        NextActionType.review_or_enrich,
        "Insufficient data; enrich profile or verify email before outreach.",
    )


def recompute_next_action_for_lead(db: Session, lead: LeadORM) -> Tuple[NextActionType, str]:
    """
    Recompute and save next best action for a lead
    
    Returns: (action_type, reason)
    """
    ctx = build_lead_context(db, lead)
    action, reason = decide_next_action(ctx)
    
    lead.next_action = action.value
    lead.next_action_reason = reason
    lead.next_action_last_calculated_at = datetime.utcnow()
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    logger.info(f"Recomputed next action for lead {lead.id}: {action.value} - {reason}")
    
    return action, reason


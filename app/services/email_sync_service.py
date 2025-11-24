"""Email sync service: Parse and classify inbound/outbound emails"""
import logging
import re
import email
from email.header import decode_header
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.orm_email_sync import EmailMessageORM, EmailDirection, EmailSyncConfigORM
from app.core.orm_campaigns import CampaignLeadORM, CampaignORM
from app.core.orm import LeadORM
from app.services.activity_logger import log_activity, ActivityType

logger = logging.getLogger(__name__)


def decode_email_header(header_value: str) -> str:
    """Decode email header (handles encoded-words)"""
    if not header_value:
        return ""
    
    try:
        decoded_parts = decode_header(header_value)
        decoded_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_str += part
        return decoded_str.strip()
    except:
        return str(header_value)


def parse_email_message(raw_email: str) -> Dict[str, Any]:
    """
    Parse raw email string into structured data
    
    Returns:
        Dict with parsed email fields
    """
    try:
        msg = email.message_from_string(raw_email)
        
        # Extract headers
        message_id = msg.get("Message-ID", "").strip()
        in_reply_to = msg.get("In-Reply-To", "").strip()
        references = msg.get("References", "").strip()
        subject = decode_email_header(msg.get("Subject", ""))
        
        # Extract addresses
        from_email = decode_email_header(msg.get("From", ""))
        to_email = decode_email_header(msg.get("To", ""))
        cc_email = decode_email_header(msg.get("Cc", ""))
        bcc_email = decode_email_header(msg.get("Bcc", ""))
        
        # Extract custom headers (for campaign/lead mapping)
        campaign_id_header = msg.get("X-Bidec-Campaign", "").strip()
        lead_id_header = msg.get("X-Bidec-Lead", "").strip()
        
        # Extract body
        body_text = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except:
                        body_text = str(part.get_payload())
                elif content_type == "text/html":
                    try:
                        body_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except:
                        body_html = str(part.get_payload())
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                try:
                    body_text = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                except:
                    body_text = str(msg.get_payload())
            elif content_type == "text/html":
                try:
                    body_html = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                except:
                    body_html = str(msg.get_payload())
        
        # Create snippet (first 2000 chars)
        snippet_text = body_text or body_html or ""
        snippet = snippet_text[:2000].replace("\n", " ").strip()
        
        # Extract email addresses from From/To fields
        from_addr = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_email)
        from_addr = from_addr.group() if from_addr else from_email
        
        to_addr = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', to_email)
        to_addr = to_addr.group() if to_addr else to_email
        
        return {
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": references,
            "subject": subject,
            "from_email": from_addr,
            "to_email": to_addr,
            "cc_email": cc_email,
            "bcc_email": bcc_email,
            "body_text": body_text,
            "body_html": body_html,
            "snippet": snippet,
            "raw_headers": str(msg.items()),
            "campaign_id_header": campaign_id_header,
            "lead_id_header": lead_id_header,
        }
    except Exception as e:
        logger.error(f"Error parsing email: {e}", exc_info=True)
        raise


def classify_email(parsed: Dict[str, Any]) -> Dict[str, bool]:
    """
    Classify email as bounce, unsubscribe, reply, or out-of-office
    
    Returns:
        Dict with classification flags
    """
    subject_lower = (parsed.get("subject") or "").lower()
    body_lower = (parsed.get("body_text") or "").lower()
    from_email_lower = (parsed.get("from_email") or "").lower()
    
    is_bounce = False
    is_unsubscribe = False
    is_reply = False
    is_ooo = False
    
    # Bounce detection
    bounce_indicators = [
        "mailer-daemon",
        "postmaster",
        "undeliverable",
        "delivery status notification",
        "delivery failure",
        "message undeliverable",
        "returned mail",
        "failure notice",
    ]
    
    if any(indicator in from_email_lower for indicator in ["mailer-daemon", "postmaster"]):
        is_bounce = True
    elif any(indicator in subject_lower for indicator in bounce_indicators):
        is_bounce = True
    elif "5.1.1" in body_lower or "5.2.2" in body_lower or "550" in body_lower:
        is_bounce = True
    
    # Out of office detection
    ooo_indicators = [
        "out of office",
        "out of the office",
        "automatic reply",
        "auto-reply",
        "vacation",
        "away from office",
        "i am currently out",
        "i will be out",
    ]
    
    if any(indicator in subject_lower for indicator in ooo_indicators):
        is_ooo = True
    elif any(indicator in body_lower for indicator in ooo_indicators):
        is_ooo = True
    
    # Unsubscribe detection
    unsubscribe_indicators = [
        "unsubscribe",
        "remove me",
        "opt out",
        "opt-out",
        "remove from list",
        "stop sending",
    ]
    
    if any(indicator in body_lower for indicator in unsubscribe_indicators):
        is_unsubscribe = True
    
    # Reply detection (has In-Reply-To or References, and not a bounce/OOO)
    if parsed.get("in_reply_to") or parsed.get("references"):
        if not is_bounce and not is_ooo:
            is_reply = True
    
    return {
        "is_bounce": is_bounce,
        "is_unsubscribe": is_unsubscribe,
        "is_reply": is_reply,
        "is_ooo": is_ooo,
    }


def map_email_to_campaign_lead(
    db: Session,
    parsed: Dict[str, Any],
    workspace_id: int,
    organization_id: int,
) -> Optional[Tuple[CampaignORM, LeadORM, CampaignLeadORM]]:
    """
    Map an email message to a campaign, lead, and CampaignLead record
    
    Returns:
        Tuple of (CampaignORM, LeadORM, CampaignLeadORM) or None
    """
    # Try header-based mapping first
    campaign_id = None
    lead_id = None
    
    if parsed.get("campaign_id_header"):
        try:
            campaign_id = int(parsed["campaign_id_header"])
        except:
            pass
    
    if parsed.get("lead_id_header"):
        try:
            lead_id = int(parsed["lead_id_header"])
        except:
            pass
    
    # If no headers, try In-Reply-To matching
    if not campaign_id or not lead_id:
        in_reply_to = parsed.get("in_reply_to")
        if in_reply_to:
            # Find original outbound message
            original = db.query(EmailMessageORM).filter(
                EmailMessageORM.message_id == in_reply_to,
                EmailMessageORM.workspace_id == workspace_id,
                EmailMessageORM.direction == EmailDirection.outbound,
            ).first()
            
            if original:
                campaign_id = original.campaign_id
                lead_id = original.lead_id
    
    # Fallback: match by email address and recent campaign
    if not campaign_id or not lead_id:
        from_email = parsed.get("from_email", "")
        if from_email:
            # Find lead by email
            lead = db.query(LeadORM).filter(
                LeadORM.organization_id == organization_id,
                LeadORM.workspace_id == workspace_id,
                LeadORM.contact_person_email.ilike(f"%{from_email}%"),
            ).first()
            
            if lead:
                lead_id = lead.id
                # Find most recent campaign for this lead
                campaign_lead = db.query(CampaignLeadORM).filter(
                    CampaignLeadORM.lead_id == lead_id,
                    CampaignLeadORM.sent == True,
                ).order_by(CampaignLeadORM.sent_at.desc()).first()
                
                if campaign_lead:
                    campaign_id = campaign_lead.campaign_id
    
    # Load objects
    if campaign_id and lead_id:
        campaign = db.query(CampaignORM).filter(CampaignORM.id == campaign_id).first()
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        
        if campaign and lead:
            campaign_lead = db.query(CampaignLeadORM).filter(
                CampaignLeadORM.campaign_id == campaign_id,
                CampaignLeadORM.lead_id == lead_id,
            ).first()
            
            if campaign_lead:
                return (campaign, lead, campaign_lead)
    
    return None


def process_inbound_email(
    db: Session,
    raw_email: str,
    workspace_id: int,
    organization_id: int,
) -> EmailMessageORM:
    """
    Process an inbound email: parse, classify, and update campaign outcomes
    
    Returns:
        EmailMessageORM record
    """
    # Parse email
    parsed = parse_email_message(raw_email)
    
    # Classify
    classification = classify_email(parsed)
    
    # Determine direction (inbound for replies/bounces)
    direction = EmailDirection.inbound
    
    # Create email message record
    email_msg = EmailMessageORM(
        workspace_id=workspace_id,
        organization_id=organization_id,
        direction=direction,
        message_id=parsed.get("message_id"),
        in_reply_to=parsed.get("in_reply_to"),
        references=parsed.get("references"),
        subject=parsed.get("subject"),
        from_email=parsed.get("from_email", ""),
        to_email=parsed.get("to_email", ""),
        cc_email=parsed.get("cc_email"),
        bcc_email=parsed.get("bcc_email"),
        body_text=parsed.get("body_text"),
        body_html=parsed.get("body_html"),
        snippet=parsed.get("snippet"),
        raw_headers=parsed.get("raw_headers"),
        is_bounce=classification["is_bounce"],
        is_unsubscribe=classification["is_unsubscribe"],
        is_reply=classification["is_reply"],
        is_ooo=classification["is_ooo"],
    )
    
    db.add(email_msg)
    db.flush()
    
    # Map to campaign and lead
    mapping = map_email_to_campaign_lead(
        db=db,
        parsed=parsed,
        workspace_id=workspace_id,
        organization_id=organization_id,
    )
    
    if mapping:
        campaign, lead, campaign_lead = mapping
        email_msg.campaign_id = campaign.id
        email_msg.lead_id = lead.id
        
        # Update CampaignLead based on classification
        now = datetime.utcnow()
        
        if classification["is_bounce"]:
            campaign_lead.bounced = True
            campaign_lead.bounced_at = now
            campaign_lead.bounce_reason = parsed.get("snippet", "")[:500]
            campaign_lead.last_event_at = now
            
            # Update lead flags
            lead.has_bounced = True
            
            log_activity(
                db=db,
                workspace_id=workspace_id,
                type=ActivityType.campaign_event,
                lead_id=lead.id,
                campaign_id=campaign.id,
                meta={"event": "bounced", "reason": parsed.get("snippet", "")[:200]},
            )
        
        elif classification["is_unsubscribe"]:
            campaign_lead.unsubscribed = True
            campaign_lead.unsubscribed_at = now
            campaign_lead.last_event_at = now
            
            log_activity(
                db=db,
                workspace_id=workspace_id,
                type=ActivityType.campaign_event,
                lead_id=lead.id,
                campaign_id=campaign.id,
                meta={"event": "unsubscribed"},
            )
        
        elif classification["is_reply"] and not classification["is_ooo"]:
            campaign_lead.replied = True
            campaign_lead.replied_at = now
            campaign_lead.reply_snippet = parsed.get("snippet", "")[:500]
            campaign_lead.last_event_at = now
            
            # Update lead flags
            lead.has_replied = True
            
            log_activity(
                db=db,
                workspace_id=workspace_id,
                type=ActivityType.campaign_event,
                lead_id=lead.id,
                campaign_id=campaign.id,
                meta={"event": "replied", "snippet": parsed.get("snippet", "")[:200]},
            )
        
        db.add(campaign_lead)
        db.add(lead)
    
    email_msg.processed = True
    email_msg.processed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(email_msg)
    
    logger.info(f"Processed inbound email: {email_msg.id} - {classification}")
    
    return email_msg


"""Temporal consistency checker - track changes over time"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.orm import LeadORM, ScrapeJobORM

logger = logging.getLogger(__name__)


class ChangeTracker:
    """Track changes to leads over time"""
    
    @staticmethod
    def get_lead_changes(
        db: Session,
        lead_id: int,
        previous_job_id: Optional[int] = None
    ) -> Dict:
        """
        Compare lead's current state with previous state
        
        Returns:
            {
                "has_changes": True/False,
                "changes": [
                    {"field": "email", "old": "...", "new": "...", "type": "updated"},
                    {"field": "phone", "old": "...", "new": "...", "type": "removed"},
                ],
                "summary": "..."
            }
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return {"has_changes": False, "changes": [], "summary": "Lead not found"}
        
        # Find previous version (from previous job)
        if previous_job_id:
            # Get lead from previous job (same website)
            previous_lead = db.query(LeadORM).filter(
                LeadORM.website == lead.website,
                LeadORM.job_id == previous_job_id,
                LeadORM.organization_id == lead.organization_id
            ).first()
        else:
            # Find most recent previous job with this lead
            previous_job = db.query(ScrapeJobORM).filter(
                ScrapeJobORM.organization_id == lead.organization_id,
                ScrapeJobORM.niche == lead.niche,
                ScrapeJobORM.id < (lead.job_id or 0),
                ScrapeJobORM.status == "completed"
            ).order_by(ScrapeJobORM.created_at.desc()).first()
            
            if previous_job:
                previous_lead = db.query(LeadORM).filter(
                    LeadORM.website == lead.website,
                    LeadORM.job_id == previous_job.id,
                    LeadORM.organization_id == lead.organization_id
                ).first()
            else:
                previous_lead = None
        
        if not previous_lead:
            return {
                "has_changes": False,
                "changes": [],
                "summary": "No previous version found for comparison"
            }
        
        # Compare fields
        changes = []
        
        # Email changes
        current_emails = set(lead.emails or [])
        previous_emails = set(previous_lead.emails or [])
        
        added_emails = current_emails - previous_emails
        removed_emails = previous_emails - current_emails
        
        for email in added_emails:
            changes.append({
                "field": "email",
                "old": None,
                "new": email,
                "type": "added"
            })
        
        for email in removed_emails:
            changes.append({
                "field": "email",
                "old": email,
                "new": None,
                "type": "removed"
            })
        
        # Phone changes
        current_phones = set(lead.phones or [])
        previous_phones = set(previous_lead.phones or [])
        
        added_phones = current_phones - previous_phones
        removed_phones = previous_phones - current_phones
        
        for phone in added_phones:
            changes.append({
                "field": "phone",
                "old": None,
                "new": phone,
                "type": "added"
            })
        
        for phone in removed_phones:
            changes.append({
                "field": "phone",
                "old": phone,
                "new": None,
                "type": "removed"
            })
        
        # Address changes
        if lead.address != previous_lead.address:
            changes.append({
                "field": "address",
                "old": previous_lead.address,
                "new": lead.address,
                "type": "updated" if lead.address and previous_lead.address else ("added" if lead.address else "removed")
            })
        
        # Service tags changes
        current_services = set(lead.service_tags or [])
        previous_services = set(previous_lead.service_tags or [])
        
        added_services = current_services - previous_services
        removed_services = previous_services - current_services
        
        if added_services or removed_services:
            changes.append({
                "field": "services",
                "old": ", ".join(removed_services) if removed_services else None,
                "new": ", ".join(added_services) if added_services else None,
                "type": "updated"
            })
        
        # Website changes
        if lead.website != previous_lead.website:
            changes.append({
                "field": "website",
                "old": previous_lead.website,
                "new": lead.website,
                "type": "updated"
            })
        
        # Generate summary
        summary = ChangeTracker._generate_summary(changes)
        
        return {
            "has_changes": len(changes) > 0,
            "changes": changes,
            "summary": summary,
            "change_count": len(changes),
        }
    
    @staticmethod
    def _generate_summary(changes: List[Dict]) -> str:
        """Generate human-readable summary of changes"""
        if not changes:
            return "No changes detected"
        
        summaries = []
        
        email_changes = [c for c in changes if c["field"] == "email"]
        phone_changes = [c for c in changes if c["field"] == "phone"]
        service_changes = [c for c in changes if c["field"] == "services"]
        
        if email_changes:
            added = sum(1 for c in email_changes if c["type"] == "added")
            removed = sum(1 for c in email_changes if c["type"] == "removed")
            if added:
                summaries.append(f"{added} new email(s)")
            if removed:
                summaries.append(f"{removed} email(s) removed")
        
        if phone_changes:
            added = sum(1 for c in phone_changes if c["type"] == "added")
            removed = sum(1 for c in phone_changes if c["type"] == "removed")
            if added:
                summaries.append(f"{added} new phone(s)")
            if removed:
                summaries.append(f"{removed} phone(s) removed")
        
        if service_changes:
            summaries.append("services updated")
        
        other_changes = [c for c in changes if c["field"] not in ["email", "phone", "services"]]
        if other_changes:
            summaries.append(f"{len(other_changes)} other change(s)")
        
        return ", ".join(summaries) if summaries else "Changes detected"


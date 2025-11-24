"""Duplicate Detection Service - Finds and merges duplicate leads"""
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from difflib import SequenceMatcher
from urllib.parse import urlparse

from app.core.orm import LeadORM
from app.core.orm_duplicates import DuplicateGroupORM, DuplicateLeadORM


def normalize_email(email: str) -> str:
    """Normalize email for comparison"""
    if not email:
        return ""
    return email.lower().strip()


def normalize_domain(url: str) -> str:
    """Extract and normalize domain from URL"""
    if not url:
        return ""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Remove www. prefix
        domain = domain.replace("www.", "").lower().strip()
        return domain
    except:
        return url.lower().strip()


def normalize_name(name: str) -> str:
    """Normalize name for comparison"""
    if not name:
        return ""
    # Remove extra spaces, lowercase
    return " ".join(name.lower().split())


def string_similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0.0-1.0)"""
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def find_duplicate_groups(
    db: Session,
    organization_id: int,
    workspace_id: Optional[int] = None,
    min_confidence: float = 0.7,
) -> List[Dict]:
    """
    Find groups of duplicate leads using multiple matching strategies.
    
    Returns list of duplicate groups with confidence scores.
    """
    # Get all leads for this org/workspace
    query = db.query(LeadORM).filter(LeadORM.organization_id == organization_id)
    if workspace_id:
        query = query.filter(LeadORM.workspace_id == workspace_id)
    
    leads = query.all()
    
    if len(leads) < 2:
        return []
    
    # Build indexes for fast lookup
    email_index: Dict[str, List[LeadORM]] = {}
    domain_index: Dict[str, List[LeadORM]] = {}
    name_domain_index: Dict[Tuple[str, str], List[LeadORM]] = {}
    
    for lead in leads:
        # Index by email
        if lead.emails:
            for email in lead.emails:
                normalized = normalize_email(email)
                if normalized:
                    email_index.setdefault(normalized, []).append(lead)
        
        # Index by domain
        if lead.website:
            domain = normalize_domain(lead.website)
            if domain:
                domain_index.setdefault(domain, []).append(lead)
        
        # Index by name + domain
        if lead.name and lead.website:
            name_norm = normalize_name(lead.name)
            domain = normalize_domain(lead.website)
            if name_norm and domain:
                name_domain_index.setdefault((name_norm, domain), []).append(lead)
    
    # Find duplicates
    duplicate_groups: Dict[int, Dict] = {}
    processed_leads = set()
    
    # Strategy 1: Same email (highest confidence)
    for email, lead_list in email_index.items():
        if len(lead_list) > 1:
            lead_ids = tuple(sorted([l.id for l in lead_list]))
            if lead_ids not in processed_leads:
                group_key = lead_ids[0]
                duplicate_groups[group_key] = {
                    "leads": lead_list,
                    "confidence": 0.95,
                    "match_reason": "same_email",
                    "matched_fields": ["email"],
                }
                processed_leads.add(lead_ids)
    
    # Strategy 2: Same domain + similar name
    for (name, domain), lead_list in name_domain_index.items():
        if len(lead_list) > 1:
            # Check if already in a group
            lead_ids = tuple(sorted([l.id for l in lead_list]))
            if lead_ids not in processed_leads:
                # Calculate name similarity within the group
                similarities = []
                for i, lead1 in enumerate(lead_list):
                    for lead2 in lead_list[i+1:]:
                        sim = string_similarity(lead1.name or "", lead2.name or "")
                        similarities.append(sim)
                
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
                confidence = 0.6 + (avg_similarity * 0.3)  # 0.6-0.9 range
                
                if confidence >= min_confidence:
                    group_key = lead_ids[0]
                    if group_key not in duplicate_groups or confidence > duplicate_groups[group_key]["confidence"]:
                        duplicate_groups[group_key] = {
                            "leads": lead_list,
                            "confidence": confidence,
                            "match_reason": "same_domain_name",
                            "matched_fields": ["name", "website"],
                        }
                    processed_leads.add(lead_ids)
    
    # Strategy 3: Same domain (lower confidence, but still useful)
    for domain, lead_list in domain_index.items():
        if len(lead_list) > 1:
            lead_ids = tuple(sorted([l.id for l in lead_list]))
            if lead_ids not in processed_leads:
                # Only if names are somewhat similar
                name_similarities = []
                for i, lead1 in enumerate(lead_list):
                    for lead2 in lead_list[i+1:]:
                        if lead1.name and lead2.name:
                            sim = string_similarity(lead1.name, lead2.name)
                            name_similarities.append(sim)
                
                if name_similarities:
                    avg_sim = sum(name_similarities) / len(name_similarities)
                    confidence = 0.5 + (avg_sim * 0.2)  # 0.5-0.7 range
                else:
                    confidence = 0.5  # Same domain but no name match
                
                if confidence >= min_confidence:
                    group_key = lead_ids[0]
                    if group_key not in duplicate_groups:
                        duplicate_groups[group_key] = {
                            "leads": lead_list,
                            "confidence": confidence,
                            "match_reason": "same_domain",
                            "matched_fields": ["website"],
                        }
                    processed_leads.add(lead_ids)
    
    # Convert to list format
    result = []
    for group_data in duplicate_groups.values():
        result.append({
            "leads": [{"id": l.id, "name": l.name, "website": l.website, "emails": l.emails} for l in group_data["leads"]],
            "confidence": group_data["confidence"],
            "match_reason": group_data["match_reason"],
            "matched_fields": group_data["matched_fields"],
        })
    
    return result


def save_duplicate_groups(
    db: Session,
    organization_id: int,
    workspace_id: Optional[int],
    groups: List[Dict],
) -> List[DuplicateGroupORM]:
    """Save duplicate groups to database"""
    saved_groups = []
    
    for group_data in groups:
        # Check if group already exists
        lead_ids = [l["id"] for l in group_data["leads"]]
        existing = db.query(DuplicateGroupORM).filter(
            and_(
                DuplicateGroupORM.organization_id == organization_id,
                DuplicateGroupORM.status == "pending",
            )
        ).join(DuplicateLeadORM).filter(
            DuplicateLeadORM.lead_id.in_(lead_ids)
        ).first()
        
        if existing:
            continue  # Skip if already exists
        
        # Create new group
        group = DuplicateGroupORM(
            organization_id=organization_id,
            workspace_id=workspace_id,
            confidence_score=group_data["confidence"],
            match_reason=group_data["match_reason"],
            status="pending",
        )
        db.add(group)
        db.flush()
        
        # Add leads to group
        for lead_data in group_data["leads"]:
            duplicate_lead = DuplicateLeadORM(
                duplicate_group_id=group.id,
                lead_id=lead_data["id"],
                similarity_score=group_data["confidence"],
                matched_fields=group_data["matched_fields"],
            )
            db.add(duplicate_lead)
        
        saved_groups.append(group)
    
    db.commit()
    return saved_groups


def merge_duplicates(
    db: Session,
    group_id: int,
    canonical_lead_id: int,
    merge_fields: Optional[Dict[str, str]] = None,
) -> LeadORM:
    """
    Merge duplicate leads into a canonical lead.
    
    Args:
        group_id: The duplicate group ID
        canonical_lead_id: The lead to keep (canonical)
        merge_fields: Dict mapping field names to merge strategy ("keep_canonical", "merge_all", "keep_most_recent")
    
    Returns:
        The updated canonical lead
    """
    group = db.query(DuplicateGroupORM).filter(DuplicateGroupORM.id == group_id).first()
    if not group:
        raise ValueError(f"Duplicate group {group_id} not found")
    
    canonical = db.query(LeadORM).filter(LeadORM.id == canonical_lead_id).first()
    if not canonical:
        raise ValueError(f"Canonical lead {canonical_lead_id} not found")
    
    # Get all duplicate leads (excluding canonical)
    duplicate_leads = [
        dl.lead for dl in group.duplicates
        if dl.lead_id != canonical_lead_id
    ]
    
    # Default merge strategy
    if not merge_fields:
        merge_fields = {
            "emails": "merge_all",
            "phones": "merge_all",
            "sources": "merge_all",
            "tags": "merge_all",
            "name": "keep_canonical",
            "website": "keep_canonical",
            "address": "keep_most_recent",
        }
    
    # Merge fields
    for duplicate in duplicate_leads:
        # Merge emails
        if merge_fields.get("emails") == "merge_all":
            existing_emails = set(canonical.emails or [])
            new_emails = set(duplicate.emails or [])
            canonical.emails = list(existing_emails | new_emails)
        
        # Merge phones
        if merge_fields.get("phones") == "merge_all":
            existing_phones = set(canonical.phones or [])
            new_phones = set(duplicate.phones or [])
            canonical.phones = list(existing_phones | new_phones)
        
        # Merge sources
        if merge_fields.get("sources") == "merge_all":
            existing_sources = set(canonical.sources or [])
            new_sources = set(duplicate.sources or [])
            canonical.sources = list(existing_sources | new_sources)
            # Also update primary source if needed
            if duplicate.source and duplicate.source not in (canonical.source, ""):
                if not canonical.source:
                    canonical.source = duplicate.source
        
        # Keep most recent for address
        if merge_fields.get("address") == "keep_most_recent":
            if duplicate.address and not canonical.address:
                canonical.address = duplicate.address
            elif duplicate.address and duplicate.updated_at > canonical.updated_at:
                canonical.address = duplicate.address
    
    # Mark group as merged
    group.status = "merged"
    group.canonical_lead_id = canonical_lead_id
    
    # Delete duplicate leads
    for duplicate in duplicate_leads:
        db.delete(duplicate)
    
    db.commit()
    db.refresh(canonical)
    
    return canonical


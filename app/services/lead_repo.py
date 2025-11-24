"""Repository for lead database operations (SYNC version)"""
from typing import Iterable, List
from sqlalchemy.orm import Session

from app.core.models import Lead
from app.core.orm import LeadORM
from app.services.duplicate_detector import DuplicateDetector, normalize_domain


def upsert_leads(db: Session, leads: Iterable[Lead], job_id: int | None = None, organization_id: int | None = None, commit: bool = True) -> List[Lead]:
    """
    Simple upsert:
    - Keyed by website (and optionally niche)
    - If exists: merge emails/phones
    - If new: insert
    """
    leads_list = list(leads)
    
    # Handle empty leads list
    if not leads_list:
        return []
    
    # Build lookup maps for duplicate detection
    websites = {l.website for l in leads_list if l.website}
    domains = {normalize_domain(w) for w in websites if w}
    
    existing_map = {}  # website -> LeadORM
    existing_by_domain = {}  # normalized_domain -> LeadORM
    
    if websites or domains:
        try:
            # Query by website
            existing_leads = db.query(LeadORM).filter(
                LeadORM.website.in_(websites)
            ).all()
            
            for row in existing_leads:
                if row.website:
                    existing_map[row.website] = row
                    domain = normalize_domain(row.website)
                    if domain and domain not in existing_by_domain:
                        existing_by_domain[domain] = row
            
            # Also query by normalized domain for better matching
            if domains:
                all_existing = db.query(LeadORM).filter(LeadORM.website.isnot(None)).all()
                for row in all_existing:
                    if row.website:
                        domain = normalize_domain(row.website)
                        if domain in domains and domain not in existing_by_domain:
                            existing_by_domain[domain] = row
                            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error querying existing leads: {e}")
            # Continue with empty map if query fails

    out: List[Lead] = []

    for l in leads_list:
        if not l.website:
            # Insert without website
            orm_obj = LeadORM(
                organization_id=organization_id or 1,  # Default org if not provided
                name=l.name,
                niche=l.niche,
                website=None,
                emails=l.emails or [],
                phones=l.phones or [],
                address=l.address,
                source=l.source or "unknown",
                city=l.city,
                country=l.country,
                job_id=job_id,
            )
            db.add(orm_obj)
            db.flush()
            l.id = orm_obj.id
            out.append(l)
            continue

        # Try to find existing lead by website or domain
        existing = existing_map.get(l.website)
        if not existing and l.website:
            domain = normalize_domain(l.website)
            existing = existing_by_domain.get(domain)
        
        if existing:
            # Merge emails and phones
            existing.emails = list(set(existing.emails or []) | set(l.emails or []))
            existing.phones = list(set(existing.phones or []) | set(l.phones or []))
            
            # Merge sources
            existing_sources = set(existing.sources or [existing.source] if existing.sources else [existing.source])
            new_source = l.source or "unknown"
            existing_sources.add(new_source)
            existing.sources = list(existing_sources)
            # Keep primary source as the first one
            if not existing.source:
                existing.source = new_source
            
            # Update other fields if missing
            existing.name = existing.name or l.name
            existing.niche = existing.niche or l.niche
            existing.address = existing.address or l.address
            existing.city = existing.city or l.city
            existing.country = existing.country or l.country
            if job_id:
                existing.job_id = job_id
            orm_obj = existing
        else:
            # Insert new
            source = l.source or "unknown"
            orm_obj = LeadORM(
                organization_id=organization_id or 1,  # Default org if not provided
                name=l.name,
                niche=l.niche,
                website=l.website,
                emails=l.emails or [],
                phones=l.phones or [],
                address=l.address,
                source=source,
                sources=[source],  # Track sources array
                city=l.city,
                country=l.country,
                job_id=job_id,
            )
            db.add(orm_obj)

        db.flush()
        l.id = orm_obj.id
        out.append(l)

    # Commit all changes at once (if requested)
    if commit:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
    
    return out


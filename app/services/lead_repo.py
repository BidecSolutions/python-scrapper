"""Repository for lead database operations (SYNC version)"""
from typing import Iterable, List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.models import Lead
from app.core.orm import LeadORM
from app.services.duplicate_detector import normalize_domain


def upsert_leads(
    db: Session,
    leads: Iterable[Lead],
    job_id: int | None = None,
    organization_id: int | None = None,
    workspace_id: int | None = None,
    commit: bool = True,
) -> List[Lead]:
    """
    Simple upsert:
    - Keyed by website (and optionally niche)
    - If exists: merge emails/phones
    - If new: insert
    """
    leads_list = list(leads)

    if not leads_list:
        return []

    websites = {l.website for l in leads_list if l.website}
    domains = {normalize_domain(w) for w in websites if w}

    existing_map: dict[str, LeadORM] = {}
    existing_by_domain: dict[str | None, LeadORM] = {}

    if websites or domains:
        try:
            base_query = db.query(LeadORM)
            if organization_id:
                base_query = base_query.filter(LeadORM.organization_id == organization_id)
            if workspace_id is not None:
                base_query = base_query.filter(
                    or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None))
                )

            existing_leads = base_query.filter(LeadORM.website.in_(websites)).all()
            for row in existing_leads:
                if row.website:
                    existing_map[row.website] = row
                    domain = normalize_domain(row.website)
                    if domain and domain not in existing_by_domain:
                        existing_by_domain[domain] = row

            if domains:
                domain_query = base_query.filter(LeadORM.website.isnot(None))
                for row in domain_query.all():
                    if row.website:
                        domain = normalize_domain(row.website)
                        if domain in domains and domain not in existing_by_domain:
                            existing_by_domain[domain] = row
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Error querying existing leads: {e}")

    out: List[Lead] = []

    for lead in leads_list:
        if not lead.website:
            orm_obj = LeadORM(
                organization_id=organization_id or 1,
                workspace_id=workspace_id,
                name=lead.name,
                niche=lead.niche,
                website=None,
                emails=lead.emails or [],
                phones=lead.phones or [],
                address=lead.address,
                source=lead.source or "unknown",
                city=lead.city,
                country=lead.country,
                job_id=job_id,
            )
            db.add(orm_obj)
            db.flush()
            lead.id = orm_obj.id
            out.append(lead)
            continue

        existing = existing_map.get(lead.website)
        if not existing:
            domain = normalize_domain(lead.website)
            existing = existing_by_domain.get(domain)

        if existing:
            existing.emails = list(set(existing.emails or []) | set(lead.emails or []))
            existing.phones = list(set(existing.phones or []) | set(lead.phones or []))

            existing_sources = set(existing.sources or [])
            if existing.source:
                existing_sources.add(existing.source)
            source_value = lead.source or "unknown"
            existing_sources.add(source_value)
            existing.sources = list(existing_sources)
            if not existing.source:
                existing.source = source_value

            existing.name = existing.name or lead.name
            existing.niche = existing.niche or lead.niche
            existing.address = existing.address or lead.address
            existing.city = existing.city or lead.city
            existing.country = existing.country or lead.country
            if job_id:
                existing.job_id = job_id
            if workspace_id is not None and existing.workspace_id is None:
                existing.workspace_id = workspace_id

            orm_obj = existing
        else:
            source_value = lead.source or "unknown"
            orm_obj = LeadORM(
                organization_id=organization_id or 1,
                workspace_id=workspace_id,
                name=lead.name,
                niche=lead.niche,
                website=lead.website,
                emails=lead.emails or [],
                phones=lead.phones or [],
                address=lead.address,
                source=source_value,
                sources=[source_value],
                city=lead.city,
                country=lead.country,
                job_id=job_id,
            )
            db.add(orm_obj)

        db.flush()
        lead.id = orm_obj.id
        out.append(lead)

    if commit:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return out


"""Dashboard AI endpoints"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel

from app.core.db import get_db
from app.core.orm import LeadORM, OrganizationORM
from app.core.orm_v2 import DossierORM, PersonScoreORM
from app.api.routes_settings import get_or_create_default_org

router = APIRouter()


def _pct(part: int, total: int) -> float:
    """Calculate percentage, avoiding division by zero"""
    if not total:
        return 0.0
    return (part / total) * 100.0


class AICoverage(BaseModel):
    scored_pct: float
    enriched_pct: float
    dossier_pct: float
    next_action_pct: float


class QualityBuckets(BaseModel):
    low: int
    medium: int
    high: int


class SourceBreakdown(BaseModel):
    jobs: int
    robots: int
    manual: int


class DashboardAIStats(BaseModel):
    org_name: str
    plan: str
    leads_total: int
    leads_last_30d: int
    avg_smart_score: Optional[float]
    ai_enriched_pct: Optional[float]
    leads_with_dossier: int
    leads_with_key_people: int
    ai_coverage: AICoverage
    quality_buckets: QualityBuckets
    source_breakdown: SourceBreakdown


class DashboardLeadRow(BaseModel):
    id: int
    name: str
    niche: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    smart_score: Optional[float] = None
    next_action_label: Optional[str] = None
    dossier_updated_at: Optional[str] = None


@router.get("/dashboard/ai", response_model=DashboardAIStats)
def get_ai_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive AI dashboard statistics"""
    org = get_or_create_default_org(db)
    org_id = org.id

    # Organization name and plan
    org_name = org.name or "Workspace"
    plan_name = org.plan_tier.value if hasattr(org.plan_tier, 'value') else str(org.plan_tier) if hasattr(org, 'plan_tier') else "Free"

    # Basic lead counts
    q_leads = db.query(LeadORM).filter(LeadORM.organization_id == org_id)
    leads_total = q_leads.count()

    last_30 = datetime.utcnow() - timedelta(days=30)
    leads_last_30d = q_leads.filter(LeadORM.created_at >= last_30).count()

    # Avg smart score & buckets
    scored_leads_q = q_leads.filter(LeadORM.smart_score.isnot(None))
    scored_count = scored_leads_q.count()

    avg_smart_score = None
    if scored_count > 0:
        avg_result = scored_leads_q.with_entities(func.avg(LeadORM.smart_score)).scalar()
        if avg_result:
            avg_smart_score = float(avg_result)

    # Quality buckets (adjust thresholds as needed)
    low_count = scored_leads_q.filter(LeadORM.smart_score < 0.4).count()
    medium_count = scored_leads_q.filter(
        and_(LeadORM.smart_score >= 0.4, LeadORM.smart_score < 0.7)
    ).count()
    high_count = scored_leads_q.filter(LeadORM.smart_score >= 0.7).count()

    quality_buckets = QualityBuckets(
        low=low_count,
        medium=medium_count,
        high=high_count,
    )

    # AI-enriched leads (leads with smart_score or quality_score)
    enriched_count = scored_leads_q.count()
    ai_enriched_pct = _pct(enriched_count, leads_total) if leads_total else None

    # Dossiers
    dossiers_q = db.query(DossierORM).filter(
        DossierORM.organization_id == org_id,
        DossierORM.status == "completed",
    )
    leads_with_dossier = dossiers_q.count()

    # Key people coverage
    leads_with_key_people = 0
    try:
        # Check if person_scores table exists and has data
        key_people_query = db.query(PersonScoreORM).filter(
            PersonScoreORM.organization_id == org_id,
            PersonScoreORM.decision_maker_score >= 0.6,
        )
        leads_with_key_people = key_people_query.distinct(PersonScoreORM.lead_id).count()
    except Exception:
        # Table might not exist yet
        pass

    # Next best action coverage
    nb_action_count = q_leads.filter(LeadORM.nb_action.isnot(None)).count()

    ai_coverage = AICoverage(
        scored_pct=_pct(scored_count, leads_total),
        enriched_pct=_pct(enriched_count, leads_total),
        dossier_pct=_pct(leads_with_dossier, leads_total),
        next_action_pct=_pct(nb_action_count, leads_total),
    )

    # Source breakdown
    source_jobs = q_leads.filter(LeadORM.source == "job").count()
    source_robots = q_leads.filter(LeadORM.source == "robot").count()
    source_manual = q_leads.filter(
        or_(LeadORM.source == "manual", LeadORM.source.is_(None))
    ).count()
    
    source_breakdown = SourceBreakdown(
        jobs=source_jobs,
        robots=source_robots,
        manual=source_manual,
    )

    return DashboardAIStats(
        org_name=org_name,
        plan=plan_name,
        leads_total=leads_total,
        leads_last_30d=leads_last_30d,
        avg_smart_score=avg_smart_score,
        ai_enriched_pct=ai_enriched_pct,
        leads_with_dossier=leads_with_dossier,
        leads_with_key_people=leads_with_key_people,
        ai_coverage=ai_coverage,
        quality_buckets=quality_buckets,
        source_breakdown=source_breakdown,
    )


@router.get("/dashboard/high-value-leads", response_model=List[DashboardLeadRow])
def get_high_value_leads(db: Session = Depends(get_db)):
    """Get top 10 leads by smart score"""
    org = get_or_create_default_org(db)
    org_id = org.id

    q = (
        db.query(LeadORM)
        .filter(
            LeadORM.organization_id == org_id,
            LeadORM.smart_score.isnot(None),
        )
        .order_by(LeadORM.smart_score.desc())
        .limit(10)
    )

    rows: List[DashboardLeadRow] = []
    for lead in q:
        rows.append(
            DashboardLeadRow(
                id=lead.id,
                name=lead.name or "Unknown",
                niche=lead.niche,
                city=lead.city,
                country=lead.country,
                smart_score=float(lead.smart_score) if lead.smart_score else None,
                next_action_label=lead.nb_action,
                dossier_updated_at=None,
            )
        )

    return rows


@router.get("/dashboard/dossier-leads", response_model=List[DashboardLeadRow])
def get_dossier_leads(db: Session = Depends(get_db)):
    """Get latest leads with completed dossiers"""
    org = get_or_create_default_org(db)
    org_id = org.id

    # Join leads + dossiers
    q = (
        db.query(LeadORM, DossierORM)
        .join(DossierORM, DossierORM.lead_id == LeadORM.id)
        .filter(
            LeadORM.organization_id == org_id,
            DossierORM.organization_id == org_id,
            DossierORM.status == "completed",
        )
        .order_by(DossierORM.updated_at.desc())
        .limit(10)
    )

    rows: List[DashboardLeadRow] = []
    for lead, dossier in q:
        rows.append(
            DashboardLeadRow(
                id=lead.id,
                name=lead.name or "Unknown",
                niche=lead.niche,
                city=lead.city,
                country=lead.country,
                smart_score=float(lead.smart_score) if lead.smart_score else None,
                next_action_label=lead.nb_action,
                dossier_updated_at=dossier.updated_at.isoformat() if dossier.updated_at else None,
            )
        )

    return rows


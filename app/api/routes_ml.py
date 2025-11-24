"""ML and AI features API routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.core.orm import LeadORM, LeadFeedbackORM, OrgModelORM, OrganizationORM, PlanTier
from app.services.ml_scoring_service import MLScoringService
from app.services.segmentation_service import SegmentationService
from app.services.insights_service import InsightsService

router = APIRouter()


def get_or_create_default_org(db: Session) -> int:
    """Get or create default organization for testing"""
    org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
    
    if not org:
        org = OrganizationORM(
            name="Default Organization",
            slug="default",
            plan_tier=PlanTier.pro,
        )
        db.add(org)
        db.flush()
    
    return org.id


class FeedbackRequest(BaseModel):
    lead_id: int
    label: str  # "good", "bad", "won"


@router.post("/feedback")
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """Submit feedback on a lead for ML training"""
    org_id = get_or_create_default_org(db)
    
    # Verify lead exists and belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == payload.lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if payload.label not in ("good", "bad", "won"):
        raise HTTPException(status_code=400, detail="Label must be 'good', 'bad', or 'won'")
    
    # Check if feedback already exists
    existing = db.query(LeadFeedbackORM).filter(
        LeadFeedbackORM.lead_id == payload.lead_id,
        LeadFeedbackORM.organization_id == org_id
    ).first()
    
    if existing:
        existing.label = payload.label
    else:
        feedback = LeadFeedbackORM(
            organization_id=org_id,
            lead_id=payload.lead_id,
            label=payload.label,
        )
        db.add(feedback)
        lead.fit_label = payload.label
    
    db.commit()
    
    return {"message": "Feedback submitted successfully"}


@router.post("/train-model")
def train_model(
    org_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Train ML model for an organization"""
    if org_id is None:
        org_id = get_or_create_default_org(db)
    
    scoring_service = MLScoringService()
    result = scoring_service.train_model_for_org(db, org_id)
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough feedback samples. Need at least {MLScoringService.MIN_FEEDBACK_SAMPLES} samples."
        )
    
    return {
        "message": "Model trained successfully",
        "version": result["version"],
        "metrics": result["metrics"],
    }


@router.post("/jobs/{job_id}/score")
def score_job_leads(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Score all leads for a job using ML model"""
    org_id = get_or_create_default_org(db)
    
    # Verify job
    from app.core.orm import ScrapeJobORM
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    scoring_service = MLScoringService()
    lead_ids = [l.id for l in job.leads]
    scored_count = scoring_service.score_leads_for_org(db, org_id, lead_ids)
    
    return {
        "message": f"Scored {scored_count} leads",
        "scored_count": scored_count,
    }


@router.post("/jobs/{job_id}/segments")
def create_segments(
    job_id: int,
    num_clusters: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Create segments for a job"""
    org_id = get_or_create_default_org(db)
    
    # Verify job
    from app.core.orm import ScrapeJobORM
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    segments = SegmentationService.create_segments_for_job(db, job_id, num_clusters)
    
    return {
        "message": f"Created {len(segments)} segments",
        "segments": [
            {
                "id": s.id,
                "label": s.label,
                "description": s.description,
                "cluster_index": s.cluster_index,
            }
            for s in segments
        ],
    }


@router.post("/jobs/{job_id}/insights")
def generate_insights(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Generate market insights for a job"""
    org_id = get_or_create_default_org(db)
    
    # Verify job
    from app.core.orm import ScrapeJobORM
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    insight = InsightsService.generate_insights_for_job(db, job_id)
    
    if not insight:
        raise HTTPException(status_code=500, detail="Failed to generate insights")
    
    return {
        "text": insight.text,
        "stats": insight.stats,
        "generated_at": insight.generated_at.isoformat(),
    }


@router.get("/jobs/{job_id}/segments")
def get_job_segments(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get segments for a job"""
    org_id = get_or_create_default_org(db)
    
    from app.core.orm import ScrapeJobORM, JobSegmentORM
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    segments = db.query(JobSegmentORM).filter(JobSegmentORM.job_id == job_id).all()
    
    # Count leads per segment
    from sqlalchemy import func
    segment_counts = db.query(
        LeadORM.segment_id,
        func.count(LeadORM.id).label('count')
    ).filter(
        LeadORM.job_id == job_id,
        LeadORM.segment_id.isnot(None)
    ).group_by(LeadORM.segment_id).all()
    
    count_map = {seg_id: count for seg_id, count in segment_counts}
    
    return [
        {
            "id": s.id,
            "label": s.label,
            "description": s.description,
            "cluster_index": s.cluster_index,
            "lead_count": count_map.get(s.id, 0),
        }
        for s in segments
    ]


@router.get("/jobs/{job_id}/insights")
def get_job_insights(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get insights for a job"""
    org_id = get_or_create_default_org(db)
    
    from app.core.orm import ScrapeJobORM, JobInsightORM
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    insight = db.query(JobInsightORM).filter(JobInsightORM.job_id == job_id).first()
    
    if not insight:
        # Generate if doesn't exist
        insight = InsightsService.generate_insights_for_job(db, job_id)
    
    if not insight:
        raise HTTPException(status_code=404, detail="No insights available")
    
    return {
        "text": insight.text,
        "stats": insight.stats,
        "generated_at": insight.generated_at.isoformat(),
    }


# Active Learning endpoints
@router.get("/leads/for-labeling")
def get_leads_for_labeling(
    limit: int = 20,
    min_uncertainty: float = 0.3,
    db: Session = Depends(get_db),
):
    """Get leads that would benefit most from user feedback (active learning)"""
    from app.services.active_learning_service import ActiveLearningService
    org_id = get_or_create_default_org(db)
    
    leads = ActiveLearningService.get_leads_for_labeling(
        db, org_id, limit=limit, min_uncertainty=min_uncertainty
    )
    
    return {
        "leads": leads,
        "count": len(leads),
        "message": "These leads would benefit most from your feedback to improve AI accuracy"
    }


# Niche Classification endpoints
@router.post("/classify-niche")
def classify_niche(
    niche: str,
    use_llm: bool = True,
):
    """Classify and normalize a niche string"""
    from app.services.niche_classifier import NicheClassifier
    
    classification = NicheClassifier.classify_niche(niche, use_llm=use_llm)
    
    return {
        "raw_niche": niche,
        "canonical": classification["canonical"],
        "subspecialty": classification["subspecialty"],
        "confidence": classification["confidence"],
    }


# Account Briefing endpoints
@router.get("/leads/{lead_id}/briefing")
def get_lead_briefing(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Generate account briefing for a lead"""
    from app.services.briefing_service import BriefingService
    org_id = get_or_create_default_org(db)
    
    # Verify lead belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    briefing = BriefingService.generate_briefing(db, lead_id)
    
    if not briefing:
        raise HTTPException(status_code=500, detail="Failed to generate briefing")
    
    return briefing


# Score Explanation endpoint
@router.get("/leads/{lead_id}/explanation")
def get_score_explanation(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get AI explanation for why a lead has a certain smart score"""
    from app.services.ml_scoring_service import MLScoringService
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    explanation = MLScoringService.explain_score(db, lead_id)
    
    return {
        "explanation": explanation,
        "smart_score": float(lead.smart_score) if lead.smart_score else None,
        "rule_score": float(lead.quality_score) if lead.quality_score else None,
    }


# Custom Fields endpoints
class CustomFieldDefinition(BaseModel):
    name: str
    type: str  # "text", "boolean", "number"
    description: str


class ExtractCustomFieldsRequest(BaseModel):
    field_definitions: List[CustomFieldDefinition]


@router.post("/leads/{lead_id}/extract-custom-fields")
def extract_custom_fields(
    lead_id: int,
    payload: ExtractCustomFieldsRequest,
    db: Session = Depends(get_db),
):
    """Extract custom fields for a lead"""
    from app.services.custom_field_extractor import CustomFieldExtractor
    org_id = get_or_create_default_org(db)
    
    # Verify lead belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Convert to dict format
    field_defs = [fd.dict() for fd in payload.field_definitions]
    
    # Extract fields
    extracted = CustomFieldExtractor.extract_custom_fields(
        db, lead_id, field_defs
    )
    
    # Save to lead.custom_fields (if column exists, otherwise use meta)
    if hasattr(lead, 'custom_fields'):
        if not lead.custom_fields:
            lead.custom_fields = {}
        lead.custom_fields.update(extracted)
    else:
        # Fallback to meta
        if not lead.meta:
            lead.meta = {}
        lead.meta['custom_fields'] = extracted
    
    db.commit()
    
    return {
        "extracted_fields": extracted,
        "message": f"Extracted {len(extracted)} custom fields"
    }


# Pitch Generator endpoints
class GeneratePitchRequest(BaseModel):
    service_offering: Optional[str] = None
    tone: str = "professional"  # "professional", "friendly", "casual"


@router.post("/leads/{lead_id}/pitches")
def generate_pitches(
    lead_id: int,
    payload: GeneratePitchRequest,
    db: Session = Depends(get_db),
):
    """Generate multi-channel pitches for a lead"""
    from app.services.pitch_generator import PitchGenerator
    org_id = get_or_create_default_org(db)
    
    # Verify lead belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    pitches = PitchGenerator.generate_pitches(
        db, lead_id,
        service_offering=payload.service_offering,
        tone=payload.tone
    )
    
    if not pitches:
        raise HTTPException(status_code=500, detail="Failed to generate pitches")
    
    return pitches


# Anomaly Detection endpoints
@router.get("/jobs/{job_id}/anomaly")
def get_job_anomaly(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Detect if a job's results are anomalous"""
    from app.services.anomaly_detector import AnomalyDetector
    org_id = get_or_create_default_org(db)
    
    # Verify job belongs to org
    from app.core.orm import ScrapeJobORM
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    anomaly = AnomalyDetector.detect_job_anomaly(db, job_id)
    
    if not anomaly:
        return {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "reasons": [],
            "suggestions": [],
            "message": "Not enough data for anomaly detection"
        }
    
    return anomaly


# Change Tracking endpoints
@router.get("/leads/{lead_id}/changes")
def get_lead_changes(
    lead_id: int,
    previous_job_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get changes to a lead since last scrape"""
    from app.services.change_tracker import ChangeTracker
    org_id = get_or_create_default_org(db)
    
    # Verify lead belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    changes = ChangeTracker.get_lead_changes(db, lead_id, previous_job_id)
    
    return changes


# Service Package Inference endpoints
@router.get("/leads/{lead_id}/packages")
def get_lead_packages(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Infer service packages from a lead's website"""
    from app.services.service_package_inference import ServicePackageInference
    org_id = get_or_create_default_org(db)
    
    # Verify lead belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    packages = ServicePackageInference.infer_packages(db, lead_id)
    
    return {
        "packages": packages,
        "count": len(packages),
    }


# Website Quality endpoints
@router.get("/leads/{lead_id}/website-quality")
def get_website_quality(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get website quality score for a lead"""
    from app.services.website_quality_scorer import WebsiteQualityScorer
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if already stored in meta
    if lead.meta and "website_quality" in lead.meta:
        return lead.meta["website_quality"]
    
    # Fetch and score
    if not lead.website:
        raise HTTPException(status_code=400, detail="Lead has no website")
    
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        response = httpx.get(lead.website, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        quality = WebsiteQualityScorer.score_website(response.text, lead.website, soup)
        
        # Store in meta
        if not lead.meta:
            lead.meta = {}
        lead.meta["website_quality"] = quality
        db.commit()
        
        return quality
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to score website: {str(e)}")


# Smart Tagging endpoints
class SmartTagRequest(BaseModel):
    custom_tags: Optional[List[str]] = None


@router.post("/leads/{lead_id}/smart-tags")
def generate_smart_tags(
    lead_id: int,
    payload: Optional[SmartTagRequest] = None,
    db: Session = Depends(get_db),
):
    """Generate smart tags for a lead"""
    from app.services.smart_tagger import SmartTagger
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    custom_tags = payload.custom_tags if payload else None
    detected_tags = SmartTagger.tag_lead(db, lead_id, custom_tags)
    
    # Merge with existing tags
    if not lead.tags:
        lead.tags = []
    for tag in detected_tags:
        if tag not in lead.tags:
            lead.tags.append(tag)
    
    db.commit()
    
    return {
        "detected_tags": detected_tags,
        "all_tags": lead.tags,
        "count": len(detected_tags),
    }


# Brand Tone Analysis endpoints
@router.get("/leads/{lead_id}/tone")
def get_brand_tone(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Analyze brand tone for a lead"""
    from app.services.brand_tone_analyzer import BrandToneAnalyzer
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    tone = BrandToneAnalyzer.analyze_tone(db, lead_id)
    
    return tone


# Lifecycle Prediction endpoints
@router.get("/leads/{lead_id}/lifecycle")
def get_lifecycle_prediction(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Predict lead lifecycle stage (hot/warm/cold)"""
    from app.services.lifecycle_predictor import LifecyclePredictor
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lifecycle = LifecyclePredictor.predict_lifecycle(db, lead_id)
    
    return lifecycle


# Custom Fields Management endpoints
class CustomFieldCreate(BaseModel):
    name: str
    label: str
    type: str  # "bool", "text", "list", "number"
    description: Optional[str] = None


@router.get("/custom-fields")
def get_custom_fields(
    db: Session = Depends(get_db),
):
    """Get custom fields for organization"""
    from app.core.orm import CustomFieldORM
    org_id = get_or_create_default_org(db)
    
    fields = db.query(CustomFieldORM).filter(
        CustomFieldORM.organization_id == org_id
    ).order_by(CustomFieldORM.created_at.desc()).all()
    
    return [
        {
            "id": f.id,
            "name": f.name,
            "label": f.label,
            "type": f.type,
            "description": f.description,
            "active": f.active,
        }
        for f in fields
    ]


@router.post("/custom-fields")
def create_custom_field(
    payload: CustomFieldCreate,
    db: Session = Depends(get_db),
):
    """Create a custom field definition"""
    from app.core.orm import CustomFieldORM
    org_id = get_or_create_default_org(db)
    
    # Check if field with same name exists
    existing = db.query(CustomFieldORM).filter(
        CustomFieldORM.organization_id == org_id,
        CustomFieldORM.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Field '{payload.name}' already exists")
    
    field = CustomFieldORM(
        organization_id=org_id,
        name=payload.name,
        label=payload.label,
        type=payload.type,
        description=payload.description,
        active=True,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    
    return {
        "id": field.id,
        "name": field.name,
        "label": field.label,
        "type": field.type,
        "description": field.description,
        "active": field.active,
    }


@router.delete("/custom-fields/{field_id}")
def delete_custom_field(
    field_id: int,
    db: Session = Depends(get_db),
):
    """Delete a custom field (soft delete by setting active=False)"""
    from app.core.orm import CustomFieldORM
    org_id = get_or_create_default_org(db)
    
    field = db.query(CustomFieldORM).filter(
        CustomFieldORM.id == field_id,
        CustomFieldORM.organization_id == org_id
    ).first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    field.active = False
    db.commit()
    
    return {"message": "Field deactivated successfully"}


# Lookalike Finder endpoints
@router.get("/leads/{lead_id}/similar")
def get_similar_leads(
    lead_id: int,
    scope: str = "workspace",
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Find similar leads to a given lead"""
    from app.services.lookalike_finder import LookalikeFinder
    org_id = get_or_create_default_org(db)
    
    # Verify lead belongs to org
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    similar = LookalikeFinder.find_similar_leads(db, lead_id, scope=scope, limit=limit)
    
    return {
        "similar_leads": similar,
        "count": len(similar),
        "reference_lead": {
            "id": lead.id,
            "name": lead.name,
            "niche": lead.niche,
        },
    }


# Playbooks endpoints
@router.get("/playbooks")
def get_playbooks(
    niche: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get playbooks for organization"""
    from app.core.orm import PlaybookORM
    org_id = get_or_create_default_org(db)
    
    query = db.query(PlaybookORM).filter(PlaybookORM.organization_id == org_id)
    
    if niche:
        query = query.filter(PlaybookORM.niche == niche)
    if location:
        query = query.filter(PlaybookORM.location == location)
    
    playbooks = query.order_by(PlaybookORM.updated_at.desc()).all()
    
    return [
        {
            "id": p.id,
            "niche": p.niche,
            "location": p.location,
            "text": p.text,
            "stats": p.stats,
            "generated_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in playbooks
    ]


@router.post("/playbooks/generate")
def generate_playbook(
    niche: str,
    location: str,
    db: Session = Depends(get_db),
):
    """Generate a playbook for niche+location"""
    from app.services.playbook_service import PlaybookService
    org_id = get_or_create_default_org(db)
    
    playbook = PlaybookService.generate_playbook(db, org_id, niche, location)
    
    if not playbook:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough leads to generate playbook. Need at least 10 leads for {niche} in {location}."
        )
    
    return {
        "id": playbook.id,
        "niche": playbook.niche,
        "location": playbook.location,
        "text": playbook.text,
        "stats": playbook.stats,
        "generated_at": playbook.created_at.isoformat(),
    }


@router.get("/playbooks/{playbook_id}")
def get_playbook(
    playbook_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific playbook by ID"""
    from app.core.orm import PlaybookORM
    org_id = get_or_create_default_org(db)
    
    playbook = db.query(PlaybookORM).filter(
        PlaybookORM.id == playbook_id,
        PlaybookORM.organization_id == org_id
    ).first()
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    return {
        "id": playbook.id,
        "niche": playbook.niche,
        "location": playbook.location,
        "text": playbook.text,
        "stats": playbook.stats,
        "generated_at": playbook.created_at.isoformat(),
        "updated_at": playbook.updated_at.isoformat(),
    }


# Tech Stack endpoints
@router.get("/leads/{lead_id}/tech-stack")
def get_lead_tech_stack(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get or detect tech stack for a lead"""
    from app.services.tech_detector import TechDetector
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # If already detected, return it
    if lead.tech_stack and lead.tech_stack.get("cms"):
        return {
            "tech_stack": lead.tech_stack,
            "digital_maturity": float(lead.digital_maturity) if lead.digital_maturity else None,
        }
    
    # Otherwise, detect it
    success = TechDetector.enrich_lead_with_tech(db, lead_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to detect tech stack")
    
    db.refresh(lead)
    
    return {
        "tech_stack": lead.tech_stack or {},
        "digital_maturity": float(lead.digital_maturity) if lead.digital_maturity else None,
    }


# QA Detector endpoints
@router.post("/leads/{lead_id}/qa-check")
def run_qa_check(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Run QA check on a lead"""
    from app.services.qa_detector import QADetector
    org_id = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    success = QADetector.check_lead_quality(db, lead_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="QA check failed")
    
    db.refresh(lead)
    
    return {
        "qa_status": lead.qa_status,
        "qa_reason": lead.qa_reason,
    }


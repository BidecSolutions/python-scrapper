"""Lookalike service - find similar leads/companies"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_
import numpy as np

from app.core.orm_lookalike import LookalikeJobORM, LookalikeCandidateORM, LookalikeJobStatus
from app.core.orm import LeadORM
from app.core.orm_companies import CompanyORM
from app.core.orm_segments import SegmentORM
from app.core.orm_lists import LeadListORM
from app.services.lookalike_embedding import (
    compute_lead_embedding,
    compute_company_embedding,
    compute_profile_embedding,
    cosine_similarity,
    compute_reason_vector,
)

logger = logging.getLogger(__name__)


def find_lookalikes(
    db: Session,
    job: LookalikeJobORM,
    min_score: float = 0.7,
    max_results: int = 1000,
    filters: Optional[Dict[str, Any]] = None,
) -> List[LookalikeCandidateORM]:
    """
    Find lookalike candidates for a job.
    
    Args:
        db: Database session
        job: LookalikeJobORM instance
        min_score: Minimum similarity score (0-1)
        max_results: Maximum number of candidates to return
        filters: Optional filters (country, size_range, etc.)
    
    Returns:
        List of LookalikeCandidateORM instances
    """
    if not job.profile_embedding:
        logger.error(f"Job {job.id} has no profile embedding")
        return []
    
    profile_emb = np.array(job.profile_embedding)
    
    # Get positive example lead IDs to exclude
    positive_lead_ids = []
    if job.source_segment_id:
        segment = db.query(SegmentORM).filter(SegmentORM.id == job.source_segment_id).first()
        if segment:
            # Get leads matching segment (simplified - would need proper segment filter logic)
            positive_lead_ids = [l.id for l in db.query(LeadORM).filter(
                LeadORM.workspace_id == job.workspace_id
            ).limit(1000).all()]  # Simplified - should apply segment filters
    elif job.source_list_id:
        list_obj = db.query(LeadListORM).filter(LeadListORM.id == job.source_list_id).first()
        if list_obj:
            # Get leads from list via list_leads relationship
            from app.core.orm_lists import LeadListLeadORM
            list_leads = db.query(LeadListLeadORM).filter(
                LeadListLeadORM.list_id == job.source_list_id
            ).all()
            positive_lead_ids = [ll.lead_id for ll in list_leads if ll.lead_id]
    
    # Query all leads in workspace (excluding positive examples)
    query = db.query(LeadORM).filter(
        LeadORM.workspace_id == job.workspace_id,
    )
    
    if positive_lead_ids:
        query = query.filter(~LeadORM.id.in_(positive_lead_ids))
    
    # Apply filters
    if filters:
        if filters.get("country"):
            query = query.filter(LeadORM.country == filters["country"])
        if filters.get("min_size") or filters.get("max_size"):
            # Would need company join for size filtering
            pass
    
    all_leads = query.limit(10000).all()  # Limit for performance
    
    candidates = []
    
    for lead in all_leads:
        # Get company if available
        company = None
        if lead.company_id:
            company = db.query(CompanyORM).filter(CompanyORM.id == lead.company_id).first()
        
        # Compute embedding
        lead_emb = compute_lead_embedding(lead, company)
        
        # Compute similarity
        score = cosine_similarity(profile_emb, lead_emb)
        
        if score >= min_score:
            # Compute reason vector
            reason = compute_reason_vector(profile_emb, lead_emb)
            
            candidate = LookalikeCandidateORM(
                job_id=job.id,
                workspace_id=job.workspace_id,
                lead_id=lead.id,
                company_id=lead.company_id,
                score=float(score),
                reason_vector=reason,
            )
            candidates.append(candidate)
    
    # Sort by score descending
    candidates.sort(key=lambda c: c.score, reverse=True)
    
    # Limit results
    candidates = candidates[:max_results]
    
    return candidates


def build_lookalike_profile(
    db: Session,
    job: LookalikeJobORM,
) -> Optional[np.ndarray]:
    """
    Build profile embedding from positive examples.
    
    Returns the centroid embedding, or None if no examples found.
    """
    positive_leads = []
    weights = []
    
    # Get positive leads based on source
    if job.source_segment_id:
        segment = db.query(SegmentORM).filter(SegmentORM.id == job.source_segment_id).first()
        if segment:
            # Get leads matching segment - filter for "good" leads (high score, positive feedback)
            # Note: has_replied might not exist - using health_score and fit_label instead
            positive_leads = db.query(LeadORM).filter(
                LeadORM.workspace_id == job.workspace_id,
                or_(
                    LeadORM.fit_label == "good",
                    LeadORM.fit_label == "won",
                    LeadORM.health_score >= 70,
                )
            ).limit(500).all()
    elif job.source_list_id:
        list_obj = db.query(LeadListORM).filter(LeadListORM.id == job.source_list_id).first()
        if list_obj:
            # Get leads from list via list_leads relationship
            from app.core.orm_lists import LeadListLeadORM
            list_leads = db.query(LeadListLeadORM).filter(
                LeadListLeadORM.list_id == job.source_list_id
            ).all()
            lead_ids = [ll.lead_id for ll in list_leads if ll.lead_id]
            if lead_ids:
                positive_leads = db.query(LeadORM).filter(LeadORM.id.in_(lead_ids)).all()
            else:
                positive_leads = []
    
    if not positive_leads:
        logger.warning(f"No positive leads found for job {job.id}")
        return None
    
    # Compute embeddings for positive leads
    embeddings = []
    for lead in positive_leads:
        company = None
        if lead.company_id:
            company = db.query(CompanyORM).filter(CompanyORM.id == lead.company_id).first()
        
        emb = compute_lead_embedding(lead, company)
        embeddings.append(emb)
        
        # Weight: higher for won/good fit, lower for just high score
        if hasattr(lead, 'fit_label') and lead.fit_label == "won":
            weights.append(3.0)
        elif hasattr(lead, 'fit_label') and lead.fit_label == "good":
            weights.append(2.0)
        elif hasattr(lead, 'health_score') and lead.health_score and float(lead.health_score) >= 80:
            weights.append(1.5)
        else:
            weights.append(1.0)
    
    if not embeddings:
        return None
    
    # Compute centroid
    profile = compute_profile_embedding(embeddings, weights)
    
    # Update job
    job.positive_lead_count = len(positive_leads)
    job.profile_embedding = profile.tolist()  # Convert to list for JSON storage
    
    return profile


"""Embedding service for computing lead/company feature vectors"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.orm import LeadORM
from app.core.orm_companies import CompanyORM

logger = logging.getLogger(__name__)

# Embedding dimension (can be adjusted)
EMBEDDING_DIM = 256


def compute_company_embedding(company: CompanyORM) -> np.ndarray:
    """
    Compute feature embedding for a company.
    
    Returns a normalized vector of size EMBEDDING_DIM.
    """
    # Initialize embedding vector
    embedding = np.zeros(EMBEDDING_DIM)
    idx = 0
    
    # Industry encoding (one-hot style, using hash)
    if company.industry:
        industry_hash = hash(company.industry) % 50
        embedding[idx + (industry_hash % 20)] = 1.0
    idx += 20
    
    # Employee size bucket (parse from string like "11-50" or use keywords)
    if company.size:
        size_str = company.size.lower()
        if "1-10" in size_str or "solo" in size_str:
            size_idx = 0
        elif "11-50" in size_str or "small" in size_str:
            size_idx = 1
        elif "51-200" in size_str or "medium" in size_str:
            size_idx = 2
        elif "201-1000" in size_str or "large" in size_str:
            size_idx = 3
        elif "1000+" in size_str or "enterprise" in size_str:
            size_idx = 4
        else:
            size_idx = 0
        if idx + size_idx < EMBEDDING_DIM:
            embedding[idx + size_idx] = 1.0
    idx += 5
    
    # Geography (country hash)
    if company.country:
        country_hash = hash(company.country) % 30
        embedding[idx + (country_hash % 30)] = 1.0
    idx += 30
    
    # Tech stack features (from relationship)
    if hasattr(company, 'tech_stack') and company.tech_stack:
        tech_items = [t.product_name for t in company.tech_stack[:20]] if hasattr(company.tech_stack, '__iter__') else []
        for tech in tech_items:
            tech_hash = hash(str(tech).lower()) % 50
            if idx + (tech_hash % 20) < EMBEDDING_DIM:
                embedding[idx + (tech_hash % 20)] = 1.0
    idx += 20
    
    # Intent signals (from relationship)
    if hasattr(company, 'intent_signals') and company.intent_signals:
        intent_items = [i.type for i in company.intent_signals[:10]] if hasattr(company.intent_signals, '__iter__') else []
        for intent in intent_items:
            intent_hash = hash(str(intent).lower()) % 30
            if idx + (intent_hash % 20) < EMBEDDING_DIM:
                embedding[idx + (intent_hash % 20)] = 1.0
    idx += 20
    
    # Fill remaining dimensions with random projection of existing features
    # This helps create a more distributed representation
    if idx < EMBEDDING_DIM:
        # Use a simple projection of existing features
        existing_features = embedding[:idx]
        if np.sum(existing_features) > 0:
            # Project to remaining dimensions
            projection = np.random.randn(idx, EMBEDDING_DIM - idx) * 0.1
            embedding[idx:] = np.dot(existing_features, projection)
    
    # Normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding


def compute_lead_embedding(lead: LeadORM, company: Optional[CompanyORM] = None) -> np.ndarray:
    """
    Compute feature embedding for a lead.
    
    Combines company features with lead-specific features (title, role, etc.).
    """
    # Start with company embedding if available
    if company:
        embedding = compute_company_embedding(company)
    else:
        embedding = np.zeros(EMBEDDING_DIM)
    
    # Lead-specific features (add to existing embedding)
    lead_features = np.zeros(EMBEDDING_DIM)
    idx = 128  # Start adding lead features after company features
    
    # Title/seniority encoding
    title = lead.title or lead.contact_person_role
    if title:
        title_lower = title.lower()
        
        # Seniority level
        if any(kw in title_lower for kw in ["ceo", "founder", "co-founder", "owner"]):
            lead_features[idx] = 1.0  # C-level
        elif any(kw in title_lower for kw in ["vp", "vice president", "head of"]):
            lead_features[idx + 1] = 1.0  # VP-level
        elif any(kw in title_lower for kw in ["director", "head"]):
            lead_features[idx + 2] = 1.0  # Director
        elif any(kw in title_lower for kw in ["manager", "lead"]):
            lead_features[idx + 3] = 1.0  # Manager
        else:
            lead_features[idx + 4] = 1.0  # IC/Other
        
        # Role family
        if any(kw in title_lower for kw in ["sales", "revenue", "business development"]):
            lead_features[idx + 5] = 1.0
        elif any(kw in title_lower for kw in ["marketing", "growth", "demand gen"]):
            lead_features[idx + 6] = 1.0
        elif any(kw in title_lower for kw in ["product", "engineering", "tech"]):
            lead_features[idx + 7] = 1.0
        elif any(kw in title_lower for kw in ["hr", "people", "talent"]):
            lead_features[idx + 8] = 1.0
        
        # Title keywords
        title_hash = hash(title_lower) % 30
        if idx + 9 + (title_hash % 20) < EMBEDDING_DIM:
            lead_features[idx + 9 + (title_hash % 20)] = 0.5
    
    idx += 30
    
    # Engagement signals (if available)
    if hasattr(lead, 'fit_label') and lead.fit_label:
        if lead.fit_label == "won":
            lead_features[idx] = 1.0
        elif lead.fit_label == "good":
            lead_features[idx] = 0.7
    if hasattr(lead, 'health_score') and lead.health_score:
        # Normalize health score to 0-1
        lead_features[idx + 1] = min(1.0, float(lead.health_score) / 100.0)
    if hasattr(lead, 'smart_score') and lead.smart_score:
        # ML score
        lead_features[idx + 2] = min(1.0, float(lead.smart_score))
    idx += 5
    
    # Combine company and lead features
    combined = embedding * 0.7 + lead_features * 0.3  # Weight company more
    
    # Normalize
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm
    
    return combined


def compute_profile_embedding(embeddings: List[np.ndarray], weights: Optional[List[float]] = None) -> np.ndarray:
    """
    Compute centroid embedding from a list of example embeddings.
    
    Args:
        embeddings: List of embedding vectors
        weights: Optional weights for each embedding (e.g., higher weight for "won" vs "replied")
    
    Returns:
        Centroid embedding (normalized)
    """
    if not embeddings:
        return np.zeros(EMBEDDING_DIM)
    
    if weights is None:
        weights = [1.0] * len(embeddings)
    
    # Weighted mean
    weighted_sum = np.zeros(EMBEDDING_DIM)
    total_weight = sum(weights)
    
    for emb, weight in zip(embeddings, weights):
        weighted_sum += emb * weight
    
    if total_weight > 0:
        centroid = weighted_sum / total_weight
    else:
        centroid = np.mean(embeddings, axis=0)
    
    # Normalize
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
    
    return centroid


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors"""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


def compute_reason_vector(
    profile_embedding: np.ndarray,
    candidate_embedding: np.ndarray,
    feature_names: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Compute which features contributed most to similarity.
    
    For now, returns a simple breakdown based on embedding segments.
    """
    # Simple heuristic: compare segments of the embedding
    # In a real implementation, you'd track which features map to which dimensions
    
    reason = {}
    
    # Industry segment (indices 0-20)
    industry_sim = cosine_similarity(
        profile_embedding[0:20],
        candidate_embedding[0:20]
    )
    reason["industry"] = round(industry_sim, 2)
    
    # Size segment (indices 20-25)
    size_sim = cosine_similarity(
        profile_embedding[20:25],
        candidate_embedding[20:25]
    )
    reason["size"] = round(size_sim, 2)
    
    # Geography segment (indices 25-55)
    geo_sim = cosine_similarity(
        profile_embedding[25:55],
        candidate_embedding[25:55]
    )
    reason["geo"] = round(geo_sim, 2)
    
    # Tech segment (indices 55-75)
    tech_sim = cosine_similarity(
        profile_embedding[55:75],
        candidate_embedding[55:75]
    )
    reason["tech"] = round(tech_sim, 2)
    
    return reason


"""Lookalike finder service - find similar leads using embeddings"""
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import numpy as np

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class LookalikeFinder:
    """Service for finding similar leads using embeddings"""
    
    @staticmethod
    def build_lead_profile(lead: LeadORM) -> str:
        """Build a text profile for embedding generation"""
        parts = []
        
        if lead.name:
            parts.append(lead.name)
        
        location_parts = []
        if lead.city:
            location_parts.append(lead.city)
        if lead.country:
            location_parts.append(lead.country)
        if location_parts:
            parts.append(", ".join(location_parts))
        
        if lead.niche:
            parts.append(f"Niche: {lead.niche}")
        
        if lead.service_tags:
            parts.append(f"Services: {', '.join(lead.service_tags)}")
        
        if lead.tags:
            parts.append(f"Tags: {', '.join(lead.tags)}")
        
        # Add AI summary if available
        if lead.meta and "ai_summary" in lead.meta:
            parts.append(f"Summary: {lead.meta['ai_summary']}")
        
        return ". ".join(parts) + "."
    
    @staticmethod
    def generate_embedding(profile_text: str) -> Optional[List[float]]:
        """Generate embedding for a lead profile using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                logger.warning("LLM client not available for embedding generation")
                return None
            
            # For now, use a simple text-based hash as embedding (placeholder)
            # In production, use actual embedding model (OpenAI, Groq, etc.)
            import hashlib
            hash_obj = hashlib.sha256(profile_text.encode())
            # Convert to 32-dim vector (simple hash-based, replace with real embedding)
            hash_bytes = hash_obj.digest()
            embedding = [float(b) / 255.0 for b in hash_bytes[:32]]
            # Pad to 128 dims for consistency
            while len(embedding) < 128:
                embedding.append(0.0)
            embedding = embedding[:128]
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    @staticmethod
    def find_similar_leads(
        db: Session,
        lead_id: int,
        scope: str = "workspace",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find similar leads to a given lead
        
        Args:
            db: Database session
            lead_id: ID of the reference lead
            scope: "workspace" or "job"
            limit: Maximum number of similar leads to return
        
        Returns:
            List of similar leads with similarity scores
        """
        # Get reference lead
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return []
        
        # Generate embedding if not exists
        if not lead.embedding:
            profile = LookalikeFinder.build_lead_profile(lead)
            embedding = LookalikeFinder.generate_embedding(profile)
            if embedding:
                lead.embedding = embedding
                db.commit()
            else:
                logger.warning(f"Could not generate embedding for lead {lead_id}")
                return []
        
        # Build query
        query = db.query(LeadORM).filter(
            LeadORM.id != lead_id,
            LeadORM.embedding.isnot(None)
        )
        
        if scope == "job" and lead.job_id:
            query = query.filter(LeadORM.job_id == lead.job_id)
        else:
            query = query.filter(LeadORM.organization_id == lead.organization_id)
        
        # Get candidate leads
        candidates = query.all()
        
        if not candidates:
            return []
        
        # Calculate similarities
        similarities = []
        ref_embedding = lead.embedding if isinstance(lead.embedding, list) else []
        
        for candidate in candidates:
            if not candidate.embedding:
                continue
            
            cand_embedding = candidate.embedding if isinstance(candidate.embedding, list) else []
            if len(cand_embedding) != len(ref_embedding):
                continue
            
            similarity = LookalikeFinder.cosine_similarity(ref_embedding, cand_embedding)
            
            similarities.append({
                "id": candidate.id,
                "name": candidate.name,
                "website": candidate.website,
                "city": candidate.city,
                "country": candidate.country,
                "niche": candidate.niche,
                "smart_score": float(candidate.smart_score) if candidate.smart_score else None,
                "quality_score": float(candidate.quality_score) if candidate.quality_score else None,
                "similarity": similarity,
            })
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]


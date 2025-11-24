"""Contrastive Embeddings Service - Self-supervised lead representation learning"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np

from app.core.orm import LeadORM, LeadSnapshotORM
from app.core.orm_v2 import EntityORM, EntityEmbeddingORM, EntityType
from app.ai.factory import create_llm_client

logger = logging.getLogger(__name__)


class ContrastiveEmbeddingService:
    """Service for generating contrastive embeddings for leads"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using sentence transformer"""
        try:
            # For now, use a simple hash-based embedding (placeholder)
            # In production, use sentence-transformers library
            import hashlib
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            embedding = [float(b) / 255.0 for b in hash_bytes[:32]]
            # Pad to dimension
            while len(embedding) < self.dimension:
                embedding.append(0.0)
            embedding = embedding[:self.dimension]
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [e / norm for e in embedding]
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def build_lead_profile_text(self, lead: LeadORM, db: Session) -> str:
        """Build comprehensive text profile of a lead for embedding"""
        parts = []
        
        # Basic info
        if lead.name:
            parts.append(f"Company: {lead.name}")
        if lead.niche:
            parts.append(f"Industry: {lead.niche}")
        if lead.city or lead.country:
            parts.append(f"Location: {lead.city or ''}, {lead.country or ''}")
        
        # Website content
        snapshots = db.query(LeadSnapshotORM).filter(
            LeadSnapshotORM.lead_id == lead.id
        ).limit(3).all()
        
        for snapshot in snapshots:
            # Take first 500 chars of each page
            text = snapshot.text[:500] if snapshot.text else ""
            if text:
                parts.append(f"Content: {text}")
        
        # Services/tags
        if lead.metadata and lead.metadata.get("services"):
            services = ", ".join(lead.metadata["services"][:10])
            parts.append(f"Services: {services}")
        
        if lead.tags:
            tags = ", ".join(lead.tags[:10])
            parts.append(f"Tags: {tags}")
        
        # Tech stack
        if lead.tech_stack:
            if isinstance(lead.tech_stack, dict):
                tech_parts = []
                if lead.tech_stack.get("cms"):
                    tech_parts.append(f"CMS: {lead.tech_stack['cms']}")
                if lead.tech_stack.get("tools"):
                    tech_parts.append(f"Tools: {', '.join(lead.tech_stack['tools'][:5])}")
                if tech_parts:
                    parts.append(" | ".join(tech_parts))
        
        return " | ".join(parts)
    
    def generate_lead_embedding(
        self,
        db: Session,
        lead: LeadORM,
        force_regenerate: bool = False
    ) -> Optional[List[float]]:
        """Generate and store embedding for a lead"""
        # Check if embedding already exists
        from app.core.orm import LeadEmbeddingORM
        existing = db.query(LeadEmbeddingORM).filter(
            LeadEmbeddingORM.lead_id == lead.id
        ).first()
        
        if existing and not force_regenerate:
            # Return existing embedding
            if isinstance(existing.vector, list):
                return existing.vector
            return None
        
        # Build profile text
        profile_text = self.build_lead_profile_text(lead, db)
        if not profile_text:
            logger.warning(f"No profile text for lead {lead.id}")
            return None
        
        # Generate embedding
        embedding = self.generate_embedding(profile_text)
        if not embedding:
            return None
        
        # Store embedding
        if existing:
            existing.vector = embedding
            existing.model = self.model_name
            existing.dim = self.dimension
        else:
            embedding_orm = LeadEmbeddingORM(
                lead_id=lead.id,
                model=self.model_name,
                dim=self.dimension,
                vector=embedding
            )
            db.add(embedding_orm)
        
        db.commit()
        return embedding
    
    def find_similar_leads(
        self,
        db: Session,
        lead_id: int,
        organization_id: int,
        limit: int = 20,
        min_similarity: float = 0.7
    ) -> List[Tuple[LeadORM, float]]:
        """Find similar leads using cosine similarity"""
        from app.core.orm import LeadEmbeddingORM
        
        # Get reference lead and embedding
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return []
        
        ref_embedding_orm = db.query(LeadEmbeddingORM).filter(
            LeadEmbeddingORM.lead_id == lead_id
        ).first()
        
        if not ref_embedding_orm:
            # Generate embedding if missing
            self.generate_lead_embedding(db, lead)
            ref_embedding_orm = db.query(LeadEmbeddingORM).filter(
                LeadEmbeddingORM.lead_id == lead_id
            ).first()
        
        if not ref_embedding_orm:
            return []
        
        ref_embedding = ref_embedding_orm.vector if isinstance(ref_embedding_orm.vector, list) else []
        if not ref_embedding:
            return []
        
        # Get all other leads with embeddings
        other_embeddings = db.query(LeadEmbeddingORM, LeadORM).join(
            LeadORM, LeadEmbeddingORM.lead_id == LeadORM.id
        ).filter(
            LeadORM.organization_id == organization_id,
            LeadORM.id != lead_id,
            LeadEmbeddingORM.lead_id != lead_id
        ).all()
        
        similarities = []
        ref_vec = np.array(ref_embedding)
        
        for emb_orm, candidate_lead in other_embeddings:
            cand_embedding = emb_orm.vector if isinstance(emb_orm.vector, list) else []
            if not cand_embedding or len(cand_embedding) != len(ref_embedding):
                continue
            
            cand_vec = np.array(cand_embedding)
            similarity = float(np.dot(ref_vec, cand_vec) / (np.linalg.norm(ref_vec) * np.linalg.norm(cand_vec)))
            
            if similarity >= min_similarity:
                similarities.append((candidate_lead, similarity))
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]


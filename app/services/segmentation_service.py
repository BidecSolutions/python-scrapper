"""AI segmentation service using clustering"""
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np

from app.core.orm import LeadORM, JobSegmentORM, ScrapeJobORM
from app.services.ml_feature_extractor import MLFeatureExtractor

logger = logging.getLogger(__name__)

# Try to import clustering libraries
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available for clustering")


class SegmentationService:
    """Service for clustering leads into segments"""
    
    MIN_LEADS_FOR_CLUSTERING = 10
    
    @staticmethod
    def create_segments_for_job(
        db: Session,
        job_id: int,
        num_clusters: Optional[int] = None
    ) -> List[JobSegmentORM]:
        """
        Create segments for a job using clustering
        
        Returns:
            List of created segments
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Clustering disabled: scikit-learn not available")
            return []
        
        # Get job and leads
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if not job:
            return []
        
        leads = db.query(LeadORM).filter(LeadORM.job_id == job_id).all()
        
        if len(leads) < SegmentationService.MIN_LEADS_FOR_CLUSTERING:
            logger.info(f"Not enough leads ({len(leads)}) for clustering job {job_id}")
            return []
        
        # Extract features for clustering
        feature_vectors = []
        valid_leads = []
        
        for lead in leads:
            features = MLFeatureExtractor.extract_features(lead)
            # Use a subset of features for clustering (numeric only)
            vector = [
                features.get('has_email', 0.0),
                features.get('has_phone', 0.0),
                features.get('num_emails', 0.0),
                features.get('num_phones', 0.0),
                features.get('num_social_links', 0.0),
                features.get('has_website', 0.0),
                features.get('website_https', 0.0),
                features.get('ai_score_basic', 0.0),
                features.get('num_service_tags', 0.0),
                features.get('company_size_numeric', 0.0),
                features.get('is_multi_location', 0.0),
            ]
            feature_vectors.append(vector)
            valid_leads.append(lead)
        
        if not feature_vectors:
            return []
        
        X = np.array(feature_vectors)
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine number of clusters (auto if not specified)
        if num_clusters is None:
            num_clusters = min(5, max(2, len(leads) // 5))  # 2-5 clusters based on data size
        
        # Run k-means
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Create segments
        segments = []
        for cluster_idx in range(num_clusters):
            cluster_leads = [valid_leads[i] for i, label in enumerate(cluster_labels) if label == cluster_idx]
            
            if not cluster_leads:
                continue
            
            # Generate segment name using LLM (simplified for now - use sample leads)
            segment_name, description = SegmentationService._name_segment(cluster_leads, job.niche)
            
            segment = JobSegmentORM(
                job_id=job_id,
                cluster_index=cluster_idx,
                label=segment_name,
                description=description,
            )
            db.add(segment)
            db.flush()
            
            # Assign leads to segment
            for lead in cluster_leads:
                lead.segment_id = segment.id
            
            segments.append(segment)
        
        db.commit()
        logger.info(f"Created {len(segments)} segments for job {job_id}")
        return segments
    
    @staticmethod
    def _name_segment(leads: List[LeadORM], niche: str) -> Tuple[str, str]:
        """
        Generate segment name and description using LLM
        
        Returns:
            (name, description)
        """
        # For now, use a simple heuristic
        # In production, call Groq LLM with sample leads
        
        # Collect sample data
        sample_names = [lead.name for lead in leads[:10] if lead.name]
        sample_cities = [lead.city for lead in leads[:10] if lead.city]
        has_emails = sum(1 for lead in leads if lead.emails)
        has_phones = sum(1 for lead in leads if lead.phones)
        
        # Simple heuristic-based naming
        if len(set(sample_cities)) == 1 and sample_cities[0]:
            city = sample_cities[0]
            name = f"{niche.title()} in {city}"
            description = f"Businesses in {city} with {len(leads)} leads"
        else:
            name = f"{niche.title()} Segment ({len(leads)} leads)"
            description = f"Group of {len(leads)} {niche} businesses"
        
        # Try LLM naming if available
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            if llm_client:
                prompt = f"""You are naming a segment of businesses.

Niche: {niche}
Number of leads: {len(leads)}

Sample business names:
{chr(10).join(f"- {name}" for name in sample_names[:10])}

Common cities: {', '.join(set(sample_cities[:5]))}

Provide:
1. A short name (max 6 words)
2. A 1-sentence description

Format:
Name: [name]
Description: [description]"""
                
                import asyncio
                import inspect
                if inspect.iscoroutinefunction(llm_client.chat_completion):
                    result = asyncio.run(llm_client.chat_completion([
                        {"role": "user", "content": prompt}
                    ], temperature=0.7))
                else:
                    result = llm_client.chat_completion([
                        {"role": "user", "content": prompt}
                    ], temperature=0.7)
                
                if result:
                    # Parse response
                    lines = result.split("\n")
                    for line in lines:
                        if line.startswith("Name:"):
                            name = line.replace("Name:", "").strip()
                        elif line.startswith("Description:"):
                            description = line.replace("Description:", "").strip()
        except Exception as e:
            logger.warning(f"Failed to use LLM for segment naming: {e}")
        
        return name, description


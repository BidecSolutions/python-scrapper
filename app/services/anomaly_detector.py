"""Anomaly detection for jobs and leads"""
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
import numpy as np

from app.core.orm import ScrapeJobORM, LeadORM

logger = logging.getLogger(__name__)

# Try to import sklearn
try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AnomalyDetector:
    """Detect anomalies in job results"""
    
    @staticmethod
    def detect_job_anomaly(
        db: Session,
        job_id: int
    ) -> Optional[Dict]:
        """
        Detect if a job's results are anomalous compared to similar jobs
        
        Returns:
            {
                "is_anomaly": True/False,
                "anomaly_score": 0.0-1.0,
                "reasons": ["..."],
                "suggestions": ["..."]
            } or None if not enough data
        """
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if not job:
            return None
        
        # Get similar jobs (same niche, same org)
        similar_jobs = db.query(ScrapeJobORM).filter(
            ScrapeJobORM.organization_id == job.organization_id,
            ScrapeJobORM.niche == job.niche,
            ScrapeJobORM.status == "completed",
            ScrapeJobORM.id != job_id
        ).limit(20).all()
        
        if len(similar_jobs) < 3:
            # Not enough data for comparison
            return None
        
        # Calculate features for this job
        job_features = AnomalyDetector._extract_job_features(job)
        
        # Calculate features for similar jobs
        similar_features = [AnomalyDetector._extract_job_features(j) for j in similar_jobs]
        
        if not similar_features:
            return None
        
        # Use Isolation Forest for anomaly detection
        if SKLEARN_AVAILABLE:
            try:
                X = np.array(similar_features + [job_features])
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                predictions = iso_forest.fit_predict(X)
                anomaly_score = -iso_forest.score_samples([job_features])[0]  # Negative score = more anomalous
                
                is_anomaly = predictions[-1] == -1  # Last one is our job
                
                # Normalize score to 0-1
                anomaly_score = max(0.0, min(1.0, (anomaly_score + 0.5) * 2))
                
            except Exception as e:
                logger.warning(f"Anomaly detection failed: {e}")
                return AnomalyDetector._rule_based_anomaly(job, similar_jobs)
        else:
            return AnomalyDetector._rule_based_anomaly(job, similar_jobs)
        
        # Generate reasons and suggestions
        reasons = []
        suggestions = []
        
        if is_anomaly:
            # Compare metrics
            avg_leads = np.mean([j.result_count for j in similar_jobs])
            avg_success_rate = np.mean([
                (j.sites_crawled / j.total_targets) if j.total_targets and j.total_targets > 0 else 0
                for j in similar_jobs
            ])
            
            job_success_rate = (job.sites_crawled / job.total_targets) if job.total_targets and job.total_targets > 0 else 0
            
            if job.result_count < avg_leads * 0.5:
                reasons.append(f"Very low lead count ({job.result_count} vs avg {avg_leads:.0f})")
                suggestions.append("Check if sources are configured correctly")
            
            if job_success_rate < avg_success_rate * 0.5:
                reasons.append(f"Low success rate ({job_success_rate:.0%} vs avg {avg_success_rate:.0%})")
                suggestions.append("Some websites may be blocking crawlers")
            
            if job.sites_failed > job.sites_crawled:
                reasons.append("More failed sites than successful crawls")
                suggestions.append("Check network connectivity or API keys")
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 3),
            "reasons": reasons,
            "suggestions": suggestions,
        }
    
    @staticmethod
    def _extract_job_features(job: ScrapeJobORM) -> List[float]:
        """Extract numerical features from a job"""
        features = [
            float(job.result_count or 0),
            float(job.sites_crawled or 0),
            float(job.sites_failed or 0),
            float(job.total_pages_crawled or 0),
            float((job.sites_crawled / job.total_targets) if job.total_targets and job.total_targets > 0 else 0),
            float((job.result_count / job.total_targets) if job.total_targets and job.total_targets > 0 else 0),
            float(job.duration_seconds or 0),
        ]
        return features
    
    @staticmethod
    def _rule_based_anomaly(
        job: ScrapeJobORM,
        similar_jobs: List[ScrapeJobORM]
    ) -> Dict:
        """Fallback rule-based anomaly detection"""
        is_anomaly = False
        reasons = []
        suggestions = []
        
        if not similar_jobs:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reasons": [],
                "suggestions": [],
            }
        
        avg_leads = sum(j.result_count for j in similar_jobs) / len(similar_jobs)
        
        if job.result_count < avg_leads * 0.3:
            is_anomaly = True
            reasons.append(f"Very low lead count ({job.result_count} vs avg {avg_leads:.0f})")
            suggestions.append("Check source configuration")
        
        if job.sites_failed > job.sites_crawled * 2:
            is_anomaly = True
            reasons.append("High failure rate")
            suggestions.append("Check network or API keys")
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": 0.7 if is_anomaly else 0.2,
            "reasons": reasons,
            "suggestions": suggestions,
        }


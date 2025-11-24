"""ML-based smart scoring service"""
import os
import pickle
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session

from app.core.orm import LeadORM, OrgModelORM, LeadFeedbackORM
from app.services.ml_feature_extractor import MLFeatureExtractor

logger = logging.getLogger(__name__)

# Try to import sklearn (optional dependency)
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")


class MLScoringService:
    """Service for ML-based smart scoring"""
    
    MODELS_DIR = Path("models")
    MIN_FEEDBACK_SAMPLES = 50  # Minimum feedback needed for per-org model
    
    def __init__(self):
        if not SKLEARN_AVAILABLE:
            logger.warning("ML scoring disabled: scikit-learn not installed")
        self.MODELS_DIR.mkdir(exist_ok=True)
    
    def train_model_for_org(
        self,
        db: Session,
        org_id: int,
        model_type: str = "lead_scoring"
    ) -> Optional[Dict]:
        """
        Train ML model for an organization
        
        Returns:
            Dict with model info and metrics, or None if not enough data
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Cannot train model: scikit-learn not available")
            return None
        
        # Get feedback data
        feedback_query = db.query(LeadFeedbackORM).filter(
            LeadFeedbackORM.organization_id == org_id
        ).all()
        
        if len(feedback_query) < self.MIN_FEEDBACK_SAMPLES:
            logger.info(f"Not enough feedback samples ({len(feedback_query)}) for org {org_id}. Need {self.MIN_FEEDBACK_SAMPLES}")
            return None
        
        # Build training data
        X = []
        y = []
        lead_ids = []
        
        for feedback in feedback_query:
            lead = db.query(LeadORM).filter(LeadORM.id == feedback.lead_id).first()
            if not lead:
                continue
            
            features = MLFeatureExtractor.extract_features(lead)
            feature_vector = [features.get(name, 0.0) for name in MLFeatureExtractor.get_feature_names()]
            X.append(feature_vector)
            
            # y = 1 for "good" or "won", y = 0 for "bad"
            label = 1.0 if feedback.label in ("good", "won") else 0.0
            y.append(label)
            lead_ids.append(lead.id)
        
        if len(X) < self.MIN_FEEDBACK_SAMPLES:
            return None
        
        X = np.array(X)
        y = np.array(y)
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model (start with Gradient Boosting - better than logistic regression)
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba) if len(set(y_test)) > 1 else 0.5
        
        metrics = {
            "accuracy": float(accuracy),
            "auc": float(auc),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }
        
        # Get next version
        last_model = db.query(OrgModelORM).filter(
            OrgModelORM.organization_id == org_id,
            OrgModelORM.type == model_type
        ).order_by(OrgModelORM.version.desc()).first()
        
        next_version = (last_model.version + 1) if last_model else 1
        
        # Save model
        model_path = self.MODELS_DIR / f"org_{org_id}_{model_type}_v{next_version}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        
        # Save to database
        from datetime import datetime
        org_model = OrgModelORM(
            organization_id=org_id,
            type=model_type,
            version=next_version,
            trained_at=datetime.utcnow(),
            model_path=str(model_path),
            params={"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1},
            metrics=metrics,
        )
        db.add(org_model)
        db.commit()
        
        logger.info(f"Trained model for org {org_id}: accuracy={accuracy:.3f}, auc={auc:.3f}")
        
        return {
            "version": next_version,
            "metrics": metrics,
            "model_path": str(model_path),
        }
    
    def score_lead(
        self,
        db: Session,
        lead: LeadORM,
        org_id: Optional[int] = None
    ) -> Tuple[Optional[float], Optional[int]]:
        """
        Score a lead using ML model
        
        Returns:
            (score_probability, model_version) or (None, None) if no model available
        """
        if not SKLEARN_AVAILABLE:
            return None, None
        
        org_id = org_id or lead.organization_id
        
        # Try to load org-specific model
        model_orm = db.query(OrgModelORM).filter(
            OrgModelORM.organization_id == org_id,
            OrgModelORM.type == "lead_scoring"
        ).order_by(OrgModelORM.version.desc()).first()
        
        # Fallback to global model (if exists)
        if not model_orm:
            model_orm = db.query(OrgModelORM).filter(
                OrgModelORM.organization_id == 0,  # Global model
                OrgModelORM.type == "lead_scoring"
            ).order_by(OrgModelORM.version.desc()).first()
        
        if not model_orm or not model_orm.model_path:
            return None, None
        
        # Load model
        try:
            with open(model_orm.model_path, "rb") as f:
                model = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load model from {model_orm.model_path}: {e}")
            return None, None
        
        # Extract features
        features = MLFeatureExtractor.extract_features(lead)
        feature_vector = np.array([[features.get(name, 0.0) for name in MLFeatureExtractor.get_feature_names()]])
        
        # Predict probability
        try:
            proba = model.predict_proba(feature_vector)[0, 1]  # Probability of class 1 (good fit)
            return float(proba), model_orm.version
        except Exception as e:
            logger.error(f"Failed to score lead {lead.id}: {e}")
            return None, None
    
    def score_leads_for_org(
        self,
        db: Session,
        org_id: int,
        lead_ids: Optional[List[int]] = None
    ) -> int:
        """
        Score all leads (or specific leads) for an organization
        
        Returns:
            Number of leads scored
        """
        query = db.query(LeadORM).filter(LeadORM.organization_id == org_id)
        if lead_ids:
            query = query.filter(LeadORM.id.in_(lead_ids))
        
        leads = query.all()
        scored_count = 0
        
        for lead in leads:
            score, version = self.score_lead(db, lead, org_id)
            if score is not None:
                lead.smart_score = score
                lead.smart_score_version = version
                # Map probability to label
                if score >= 0.75:
                    lead.fit_label = "high"
                elif score >= 0.4:
                    lead.fit_label = "medium"
                else:
                    lead.fit_label = "low"
                scored_count += 1
        
        db.commit()
        logger.info(f"Scored {scored_count} leads for org {org_id}")
        return scored_count


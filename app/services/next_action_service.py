"""Next Best Action service using contextual bandit"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import random

from app.core.orm import LeadORM
from app.core.orm_v2 import NextActionORM, ActionOutcomeORM, ActionType

logger = logging.getLogger(__name__)


class NextActionService:
    """Service for recommending next best actions"""
    
    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id
    
    def get_next_action_for_lead(self, lead_id: int) -> Dict[str, Any]:
        """
        Get recommended next action for a lead
        
        Args:
            lead_id: Lead ID
        
        Returns:
            Dict with action, score, and alternatives
        """
        lead = self.db.query(LeadORM).filter(
            LeadORM.organization_id == self.organization_id,
            LeadORM.id == lead_id
        ).first()
        
        if not lead:
            raise ValueError("Lead not found")
        
        # Extract features
        features = self._extract_features(lead)
        
        # Score each action (v1: simple rule-based, later: ML model)
        action_scores = self._score_actions(features, lead)
        
        # Select best action (with small exploration)
        best_action = max(action_scores.items(), key=lambda x: x[1]["score"])
        
        # Get alternatives (top 3)
        sorted_actions = sorted(action_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        alternatives = [
            {"action": action, "score": data["score"]}
            for action, data in sorted_actions[:3]
            if action != best_action[0]
        ]
        
        # Store recommendation
        self._store_recommendation(lead_id, best_action[0], best_action[1]["score"])
        
        return {
            "action": best_action[0],
            "score": best_action[1]["score"],
            "reason": best_action[1].get("reason", ""),
            "alternatives": alternatives
        }
    
    def _extract_features(self, lead: LeadORM) -> Dict[str, Any]:
        """Extract features for action selection"""
        # Compute has_email, has_phone, has_social from lead data
        has_email = bool(lead.emails and len(lead.emails) > 0 and any(e for e in lead.emails if e))
        has_phone = bool(lead.phones and len(lead.phones) > 0 and any(p for p in lead.phones if p))
        has_social = bool(
            (lead.social_links and len(lead.social_links) > 0) or
            (lead.meta and isinstance(lead.meta, dict) and lead.meta.get("social_links"))
        )
        
        return {
            "smart_score": float(lead.smart_score) if lead.smart_score else 0.5,
            "quality_score": float(lead.quality_score) if lead.quality_score else 0.5,
            "digital_maturity": float(lead.digital_maturity) if lead.digital_maturity else 0.5,
            "has_email": has_email,
            "has_phone": has_phone,
            "has_social": has_social,
            "days_since_created": (datetime.utcnow() - lead.created_at).days if lead.created_at else 0,
        }
    
    def _score_actions(self, features: Dict[str, Any], lead: LeadORM) -> Dict[str, Dict[str, Any]]:
        """Score each possible action"""
        scores = {}
        
        # Email Template A (warm, personal)
        email_a_score = 0.5
        if features["has_email"]:
            email_a_score += 0.3
        if features["smart_score"] > 0.7:
            email_a_score += 0.2
        if features["digital_maturity"] > 0.6:
            email_a_score += 0.1
        scores[ActionType.email_template_a] = {
            "score": min(email_a_score, 1.0),
            "reason": "Email available and lead shows high engagement potential"
        }
        
        # Email Template B (value-focused)
        email_b_score = 0.4
        if features["has_email"]:
            email_b_score += 0.3
        if features["quality_score"] > 0.7:
            email_b_score += 0.2
        if features["days_since_created"] < 7:
            email_b_score += 0.1
        scores[ActionType.email_template_b] = {
            "score": min(email_b_score, 1.0),
            "reason": "Recent high-quality lead with email contact"
        }
        
        # LinkedIn DM
        linkedin_score = 0.3
        if features["has_social"]:
            linkedin_score += 0.4
        if features["smart_score"] > 0.6:
            linkedin_score += 0.2
        scores[ActionType.linkedin_dm] = {
            "score": min(linkedin_score, 1.0),
            "reason": "Social presence detected, good for personalized outreach"
        }
        
        # Skip (low priority)
        skip_score = 0.1
        if features["smart_score"] < 0.3:
            skip_score = 0.5
        if not features["has_email"] and not features["has_phone"] and not features["has_social"]:
            skip_score = 0.6
        scores[ActionType.skip] = {
            "score": skip_score,
            "reason": "Low engagement potential or missing contact info"
        }
        
        return scores
    
    def _store_recommendation(self, lead_id: int, action: str, score: float):
        """Store recommendation in database"""
        next_action = self.db.query(NextActionORM).filter(
            NextActionORM.organization_id == self.organization_id,
            NextActionORM.lead_id == lead_id
        ).first()
        
        if next_action:
            next_action.action = ActionType(action)
            next_action.confidence = score
            next_action.updated_at = datetime.utcnow()
        else:
            next_action = NextActionORM(
                organization_id=self.organization_id,
                lead_id=lead_id,
                action=ActionType(action),
                confidence=score,
                suggested_at=datetime.utcnow()
            )
            self.db.add(next_action)
        
        # Also update lead record
        lead = self.db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if lead:
            lead.nb_action = action
            lead.nb_action_score = score
            lead.nb_action_generated_at = datetime.utcnow()
    
    def record_action_outcome(
        self,
        lead_id: int,
        action: str,
        outcome: Optional[str] = None,
        suggested_by_ai: bool = False
    ):
        """Record an action taken and its outcome"""
        action_outcome = ActionOutcomeORM(
            organization_id=self.organization_id,
            lead_id=lead_id,
            action=ActionType(action),
            action_taken_at=datetime.utcnow(),
            outcome=outcome,
            suggested_by_ai=suggested_by_ai,
            reward=self._calculate_reward(outcome) if outcome else None
        )
        self.db.add(action_outcome)
        self.db.commit()
    
    def _calculate_reward(self, outcome: str) -> float:
        """Calculate reward for RL training"""
        reward_map = {
            "won": 1.0,
            "booked_call": 0.8,
            "replied": 0.6,
            "opened": 0.3,
            "no_response": 0.0,
            "bounced": -0.2,
            "unsubscribed": -0.5,
        }
        return reward_map.get(outcome, 0.0)
    
    def get_bulk_actions(self, lead_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get next actions for multiple leads"""
        results = {}
        for lead_id in lead_ids:
            try:
                results[lead_id] = self.get_next_action_for_lead(lead_id)
            except Exception as e:
                logger.error(f"Failed to get action for lead {lead_id}: {e}")
                results[lead_id] = {"action": "skip", "score": 0.0, "reason": "Error"}
        return results


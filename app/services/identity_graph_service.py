"""Identity Graph service for decision makers and company relationships"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.orm_v2 import EntityORM, EdgeORM, PersonScoreORM, EntityType, EdgeType

logger = logging.getLogger(__name__)


class IdentityGraphService:
    """Service for managing identity graph and decision maker scoring"""
    
    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id
    
    def get_or_create_company_entity(self, lead) -> EntityORM:
        """Get or create company entity for a lead"""
        # Try to find existing company entity
        external_id = lead.website or f"lead_{lead.id}"
        
        entity = self.db.query(EntityORM).filter(
            EntityORM.organization_id == self.organization_id,
            EntityORM.type == EntityType.company,
            EntityORM.external_id == external_id
        ).first()
        
        if not entity:
            entity = EntityORM(
                organization_id=self.organization_id,
                type=EntityType.company,
                external_id=external_id,
                name=lead.name,
                url=lead.website,
                data={
                    "niche": lead.niche,
                    "city": lead.city,
                    "country": lead.country,
                }
            )
            self.db.add(entity)
            self.db.flush()
        
        return entity
    
    def add_person_to_company(
        self,
        company_entity: EntityORM,
        person_name: str,
        title: str,
        linkedin_url: Optional[str] = None,
        person_data: Optional[Dict[str, Any]] = None
    ) -> EntityORM:
        """Add a person entity and link to company"""
        # Create or find person entity
        external_id = linkedin_url or f"person_{person_name}_{company_entity.id}"
        
        person = self.db.query(EntityORM).filter(
            EntityORM.organization_id == self.organization_id,
            EntityORM.type == EntityType.person,
            EntityORM.external_id == external_id
        ).first()
        
        if not person:
            person = EntityORM(
                organization_id=self.organization_id,
                type=EntityType.person,
                external_id=external_id,
                name=person_name,
                url=linkedin_url,
                data={
                    "title": title,
                    **(person_data or {})
                }
            )
            self.db.add(person)
            self.db.flush()
        
        # Create edge if not exists
        edge = self.db.query(EdgeORM).filter(
            EdgeORM.organization_id == self.organization_id,
            EdgeORM.src_entity_id == person.id,
            EdgeORM.dst_entity_id == company_entity.id,
            EdgeORM.type == EdgeType.works_at
        ).first()
        
        if not edge:
            edge = EdgeORM(
                organization_id=self.organization_id,
                src_entity_id=person.id,
                dst_entity_id=company_entity.id,
                type=EdgeType.works_at,
                weight=1.0
            )
            self.db.add(edge)
        
        return person
    
    def score_decision_maker(self, person_entity: EntityORM, company_entity: EntityORM, lead_id: Optional[int] = None) -> PersonScoreORM:
        """Score a person as a decision maker"""
        title = (person_entity.data.get("title") or "").lower()
        
        score = 0.0
        role = "Influencer"
        reason_parts = []
        
        # Title-based scoring
        if any(k in title for k in ["founder", "owner", "ceo", "co-founder", "chief executive"]):
            score += 0.6
            role = "Primary"
            reason_parts.append("C-level executive")
        elif "head of" in title or "director" in title:
            score += 0.5
            role = "Primary" if score >= 0.5 else "Secondary"
            reason_parts.append("Senior leadership role")
        elif "manager" in title or "lead" in title:
            score += 0.3
            role = "Secondary"
            reason_parts.append("Management role")
        
        # Department relevance
        if any(k in title for k in ["marketing", "sales", "growth", "business development"]):
            score += 0.3
            reason_parts.append("Relevant department")
        elif any(k in title for k in ["operations", "strategy", "product"]):
            score += 0.2
            reason_parts.append("Strategic role")
        
        # Clamp score
        score = min(score, 1.0)
        
        # Generate reason
        reason = f"{person_entity.name} ({person_entity.data.get('title', 'Unknown title')})"
        if reason_parts:
            reason += f" - {', '.join(reason_parts)}"
        
        # Get or create score
        person_score = self.db.query(PersonScoreORM).filter(
            PersonScoreORM.organization_id == self.organization_id,
            PersonScoreORM.person_entity_id == person_entity.id,
            PersonScoreORM.company_entity_id == company_entity.id
        ).first()
        
        if person_score:
            person_score.decision_maker_score = score
            person_score.role = role
            person_score.reason = reason
            person_score.lead_id = lead_id
        else:
            person_score = PersonScoreORM(
                organization_id=self.organization_id,
                person_entity_id=person_entity.id,
                company_entity_id=company_entity.id,
                lead_id=lead_id,
                decision_maker_score=score,
                role=role,
                reason=reason
            )
            self.db.add(person_score)
        
        return person_score
    
    def get_key_people_for_lead(self, lead_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get key decision makers for a lead"""
        # Get company entity for lead
        lead = self.db.query(self.db.query(EntityORM).filter(
            EntityORM.organization_id == self.organization_id
        ).subquery().c).filter_by(id=lead_id).first()
        
        # For now, return dummy data - in production, query PersonScoreORM
        # This is a placeholder that will be replaced with actual graph queries
        return [
            {
                "id": 1,
                "name": "Sara Khan",
                "title": "Head of Marketing",
                "score": 0.91,
                "role": "Primary",
                "linkedin_url": "https://linkedin.com/in/sarakhan",
                "reason": "Senior marketing leader likely responsible for patient acquisition."
            },
            {
                "id": 2,
                "name": "Ahmed Ali",
                "title": "Operations Director",
                "score": 0.75,
                "role": "Secondary",
                "linkedin_url": None,
                "reason": "Operations leadership role with strategic influence."
            }
        ]


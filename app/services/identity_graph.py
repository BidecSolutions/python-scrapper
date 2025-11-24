"""Identity Graph Service - Builds and maintains entity relationships"""
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.orm import LeadORM, OrganizationORM
from app.core.orm_v2 import (
    EntityORM, EdgeORM, EntityType, EdgeType, EntityEmbeddingORM
)

logger = logging.getLogger(__name__)


class IdentityGraphService:
    """Service for building and querying the identity graph"""
    
    @staticmethod
    def create_entity_from_lead(
        db: Session,
        lead: LeadORM,
        organization_id: int
    ) -> EntityORM:
        """Create or update entity from a lead"""
        # Check if company entity already exists
        entity = db.query(EntityORM).filter(
            EntityORM.organization_id == organization_id,
            EntityORM.type == EntityType.company,
            or_(
                EntityORM.url == lead.website,
                EntityORM.name == lead.name
            )
        ).first()
        
        if not entity:
            entity = EntityORM(
                organization_id=organization_id,
                type=EntityType.company,
                name=lead.name,
                url=lead.website,
                data={
                    "niche": lead.niche,
                    "city": lead.city,
                    "country": lead.country,
                    "source": lead.source,
                }
            )
            db.add(entity)
            db.flush()
        
        # Create domain entity if website exists
        if lead.website:
            domain = IdentityGraphService._extract_domain(lead.website)
            domain_entity = IdentityGraphService._get_or_create_entity(
                db, organization_id, EntityType.domain, domain, None
            )
            
            # Create edge: company -> domain
            IdentityGraphService._create_edge_if_not_exists(
                db, organization_id, entity.id, domain_entity.id, EdgeType.same_domain
            )
        
        # Link emails and phones
        for email in (lead.emails or []):
            email_entity = IdentityGraphService._get_or_create_entity(
                db, organization_id, EntityType.email_address, email, None
            )
            IdentityGraphService._create_edge_if_not_exists(
                db, organization_id, email_entity.id, entity.id, EdgeType.email_belongs_to
            )
        
        for phone in (lead.phones or []):
            phone_entity = IdentityGraphService._get_or_create_entity(
                db, organization_id, EntityType.phone_number, phone, None
            )
            IdentityGraphService._create_edge_if_not_exists(
                db, organization_id, phone_entity.id, entity.id, EdgeType.phone_belongs_to
            )
        
        db.commit()
        return entity
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        return url.split("/")[0].split("?")[0]
    
    @staticmethod
    def _get_or_create_entity(
        db: Session,
        organization_id: int,
        entity_type: EntityType,
        name: Optional[str],
        external_id: Optional[str]
    ) -> EntityORM:
        """Get or create an entity"""
        query = db.query(EntityORM).filter(
            EntityORM.organization_id == organization_id,
            EntityORM.type == entity_type
        )
        
        if external_id:
            query = query.filter(EntityORM.external_id == external_id)
        elif name:
            query = query.filter(EntityORM.name == name)
        else:
            raise ValueError("Either name or external_id must be provided")
        
        entity = query.first()
        if not entity:
            entity = EntityORM(
                organization_id=organization_id,
                type=entity_type,
                name=name,
                external_id=external_id
            )
            db.add(entity)
            db.flush()
        
        return entity
    
    @staticmethod
    def _create_edge_if_not_exists(
        db: Session,
        organization_id: int,
        src_id: int,
        dst_id: int,
        edge_type: EdgeType,
        weight: float = 1.0
    ):
        """Create edge if it doesn't exist"""
        existing = db.query(EdgeORM).filter(
            EdgeORM.organization_id == organization_id,
            EdgeORM.src_entity_id == src_id,
            EdgeORM.dst_entity_id == dst_id,
            EdgeORM.type == edge_type
        ).first()
        
        if not existing:
            edge = EdgeORM(
                organization_id=organization_id,
                src_entity_id=src_id,
                dst_entity_id=dst_id,
                type=edge_type,
                weight=weight
            )
            db.add(edge)
    
    @staticmethod
    def get_key_people(
        db: Session,
        lead_id: int,
        organization_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get key people (decision makers) for a lead"""
        # Find company entity for this lead
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return []
        
        company_entity = db.query(EntityORM).filter(
            EntityORM.organization_id == organization_id,
            EntityORM.type == EntityType.company,
            or_(
                EntityORM.url == lead.website,
                EntityORM.name == lead.name
            )
        ).first()
        
        if not company_entity:
            return []
        
        # Find people connected via "works_at" edges
        people_edges = db.query(EdgeORM).join(
            EntityORM, EdgeORM.src_entity_id == EntityORM.id
        ).filter(
            EdgeORM.organization_id == organization_id,
            EdgeORM.dst_entity_id == company_entity.id,
            EdgeORM.type == EdgeType.works_at,
            EntityORM.type == EntityType.person
        ).order_by(EntityORM.decision_maker_score.desc().nulls_last()).limit(limit).all()
        
        result = []
        for edge in people_edges:
            person = db.query(EntityORM).filter(EntityORM.id == edge.src_entity_id).first()
            if person:
                result.append({
                    "id": person.id,
                    "name": person.name,
                    "title": person.data.get("title", ""),
                    "decision_maker_score": person.decision_maker_score or 0.0,
                    "decision_maker_role": person.decision_maker_role or "Influencer",
                    "linkedin_url": person.data.get("linkedin_url"),
                    "profile_url": person.url,
                })
        
        return result
    
    @staticmethod
    def link_social_profile(
        db: Session,
        organization_id: int,
        company_entity_id: int,
        platform: str,
        profile_id: str,
        profile_url: str,
        profile_data: Dict[str, Any]
    ) -> EntityORM:
        """Link a social profile to a company entity"""
        entity_type_map = {
            "linkedin": EntityType.linkedin_company,
            "twitter": EntityType.twitter_profile,
            "facebook": EntityType.facebook_page,
            "instagram": EntityType.instagram_profile,
        }
        
        entity_type = entity_type_map.get(platform.lower())
        if not entity_type:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Create or get social entity
        social_entity = db.query(EntityORM).filter(
            EntityORM.organization_id == organization_id,
            EntityORM.type == entity_type,
            EntityORM.external_id == profile_id
        ).first()
        
        if not social_entity:
            social_entity = EntityORM(
                organization_id=organization_id,
                type=entity_type,
                external_id=profile_id,
                name=profile_data.get("name"),
                url=profile_url,
                data=profile_data
            )
            db.add(social_entity)
            db.flush()
        
        # Create edge: company -> social profile
        IdentityGraphService._create_edge_if_not_exists(
            db, organization_id, company_entity_id, social_entity.id, EdgeType.mentions
        )
        
        db.commit()
        return social_entity


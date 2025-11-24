"""Segment filtering and matching service"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Query
from sqlalchemy import or_

from app.core.orm import LeadORM
from app.core.orm_companies import CompanyORM

logger = logging.getLogger(__name__)


def apply_segment_filter(query: Query, filter_json: Dict[str, Any], organization_id: int) -> Query:
    """
    Apply segment filter criteria to a leads query
    
    Args:
        query: Base query for LeadORM
        filter_json: Segment filter dictionary
        organization_id: Organization ID for multi-tenant filtering
    
    Returns:
        Filtered query
    """
    # Start with organization filter
    query = query.filter(LeadORM.organization_id == organization_id)
    
    # Sources filter
    if sources := filter_json.get("sources"):
        if isinstance(sources, list) and sources:
            query = query.filter(LeadORM.source.in_(sources))
    
    # Minimum score filter
    if min_score := filter_json.get("min_score"):
        if isinstance(min_score, (int, float)):
            query = query.filter(LeadORM.quality_score >= min_score)
    
    # Countries filter (requires join with company if company_id exists)
    if countries := filter_json.get("countries"):
        if isinstance(countries, list) and countries:
            # For now, filter on lead.country if it exists
            # In the future, join with CompanyORM if company_id is set
            if hasattr(LeadORM, 'country'):
                query = query.filter(LeadORM.country.in_(countries))
            else:
                # Join with company table
                query = query.join(CompanyORM, LeadORM.company_id == CompanyORM.id).filter(
                    CompanyORM.country.in_(countries)
                )
    
    # Roles filter (search in contact_person_role)
    if roles := filter_json.get("roles_contains"):
        if isinstance(roles, list) and roles:
            conditions = [LeadORM.contact_person_role.ilike(f"%{role}%") for role in roles if role]
            if conditions:
                query = query.filter(or_(*conditions))
    
    # Company sizes filter
    if company_sizes := filter_json.get("company_sizes"):
        if isinstance(company_sizes, list) and company_sizes:
            query = query.join(CompanyORM, LeadORM.company_id == CompanyORM.id).filter(
                CompanyORM.size.in_(company_sizes)
            )
    
    # Industries filter
    if industries := filter_json.get("industries"):
        if isinstance(industries, list) and industries:
            query = query.join(CompanyORM, LeadORM.company_id == CompanyORM.id).filter(
                CompanyORM.industry.in_(industries)
            )
    
    # Has email filter
    if has_email := filter_json.get("has_email"):
        if has_email:
            # Check if lead has valid email
            from app.core.orm import EmailORM, EmailVerificationStatus
            query = query.join(EmailORM, EmailORM.lead_id == LeadORM.id).filter(
                EmailORM.verify_status == EmailVerificationStatus.VALID
            )
    
    # Tags filter
    if tags := filter_json.get("tags"):
        if isinstance(tags, list) and tags:
            # Assuming tags are stored in a JSON/ARRAY field
            # This is a simplified version - adjust based on your actual tag storage
            for tag in tags:
                query = query.filter(LeadORM.tags.contains([tag]))
    
    return query


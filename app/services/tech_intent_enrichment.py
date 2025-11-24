"""Tech Stack & Intent Enrichment Service"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.orm_tech_intent import CompanyTechORM, CompanyIntentORM, TechCategory, IntentSignalType, IntentStrength
from app.core.orm_companies import CompanyORM
from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


def detect_tech_stack(domain: str, html_content: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Detect technology stack from domain/website
    
    Returns:
        List of dicts with {product_name, category, confidence, source}
    """
    detected_tech = []
    
    # Simple heuristics (in production, use BuiltWith, Wappalyzer, or similar)
    tech_patterns = {
        # CRM
        "HubSpot": {"category": TechCategory.crm, "patterns": ["hubspot", "hs-script-loader"]},
        "Salesforce": {"category": TechCategory.crm, "patterns": ["salesforce", "sfdc"]},
        "Pipedrive": {"category": TechCategory.crm, "patterns": ["pipedrive"]},
        # Marketing
        "Mailchimp": {"category": TechCategory.marketing, "patterns": ["mailchimp", "mcs-popup"]},
        "Klaviyo": {"category": TechCategory.marketing, "patterns": ["klaviyo"]},
        "HubSpot Marketing": {"category": TechCategory.marketing, "patterns": ["hs-script"]},
        # Sales Engagement
        "Lemlist": {"category": TechCategory.sales_engagement, "patterns": ["lemlist"]},
        "Instantly": {"category": TechCategory.sales_engagement, "patterns": ["instantly"]},
        "Outreach": {"category": TechCategory.sales_engagement, "patterns": ["outreach"]},
        # Billing
        "Stripe": {"category": TechCategory.billing, "patterns": ["stripe", "stripe.com/v3"]},
        "Chargebee": {"category": TechCategory.billing, "patterns": ["chargebee"]},
        # E-commerce
        "Shopify": {"category": TechCategory.ecommerce, "patterns": ["shopify"]},
        "WooCommerce": {"category": TechCategory.ecommerce, "patterns": ["woocommerce"]},
        # Infrastructure
        "AWS": {"category": TechCategory.infrastructure, "patterns": ["amazonaws", "cloudfront"]},
        "Google Cloud": {"category": TechCategory.infrastructure, "patterns": ["googlecloud", "gcp"]},
        "Azure": {"category": TechCategory.infrastructure, "patterns": ["azure"]},
    }
    
    content_lower = (html_content or "").lower()
    
    for product_name, config in tech_patterns.items():
        for pattern in config["patterns"]:
            if pattern in content_lower or pattern in domain.lower():
                detected_tech.append({
                    "product_name": product_name,
                    "category": config["category"],
                    "confidence": 0.9 if pattern in domain.lower() else 0.7,
                    "source": "internal_detection",
                })
                break  # Only add once per product
    
    return detected_tech


def detect_intent_signals(company_name: str, domain: str) -> List[Dict[str, Any]]:
    """
    Detect buying intent signals (hiring, tech changes, etc.)
    
    Returns:
        List of dicts with {type, strength, description, source}
    """
    intent_signals = []
    
    # Placeholder: In production, integrate with job boards, web analytics, etc.
    # For now, return empty - this would be populated by external APIs
    
    return intent_signals


def enrich_company_tech_intent(
    db: Session,
    company_id: int,
    organization_id: int,
    domain: Optional[str] = None,
    html_content: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Enrich company with tech stack and intent signals
    
    Returns:
        Dict with tech_count, intent_count, and created records
    """
    company = db.query(CompanyORM).filter(CompanyORM.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")
    
    domain = domain or company.domain
    if not domain:
        raise ValueError("Domain required for enrichment")
    
    # Check if already enriched (unless force_refresh)
    if not force_refresh:
        existing_tech = db.query(CompanyTechORM).filter(
            CompanyTechORM.company_id == company_id
        ).count()
        
        if existing_tech > 0:
            logger.info(f"Company {company_id} already has tech stack, skipping (use force_refresh=True)")
            return {
                "tech_count": existing_tech,
                "intent_count": db.query(CompanyIntentORM).filter(
                    CompanyIntentORM.company_id == company_id
                ).count(),
                "created": False,
            }
    
    # Detect tech stack
    detected_tech = detect_tech_stack(domain, html_content)
    
    tech_records = []
    for tech in detected_tech:
        # Check if already exists
        existing = db.query(CompanyTechORM).filter(
            CompanyTechORM.company_id == company_id,
            CompanyTechORM.product_name == tech["product_name"],
            CompanyTechORM.category == tech["category"],
        ).first()
        
        if not existing:
            tech_record = CompanyTechORM(
                company_id=company_id,
                organization_id=organization_id,
                product_name=tech["product_name"],
                category=tech["category"],
                confidence=tech["confidence"],
                source=tech["source"],
                detected_at=datetime.utcnow(),
            )
            db.add(tech_record)
            tech_records.append(tech_record)
        else:
            # Update detection time
            existing.detected_at = datetime.utcnow()
            existing.confidence = max(existing.confidence, tech["confidence"])
            tech_records.append(existing)
    
    # Detect intent signals
    intent_signals = detect_intent_signals(company.name, domain)
    
    intent_records = []
    for intent in intent_signals:
        intent_record = CompanyIntentORM(
            company_id=company_id,
            organization_id=organization_id,
            type=intent["type"],
            strength=intent.get("strength", IntentStrength.low),
            description=intent.get("description"),
            source=intent.get("source", "internal_detection"),
            detected_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=90) if intent.get("type") == IntentSignalType.hiring else None,
        )
        db.add(intent_record)
        intent_records.append(intent_record)
    
    db.commit()
    
    # Refresh to get IDs
    for record in tech_records + intent_records:
        db.refresh(record)
    
    logger.info(f"Enriched company {company_id}: {len(tech_records)} tech, {len(intent_records)} intent signals")
    
    return {
        "tech_count": len(tech_records),
        "intent_count": len(intent_records),
        "created": True,
        "tech_ids": [r.id for r in tech_records],
        "intent_ids": [r.id for r in intent_records],
    }


def get_company_tech_stack(
    db: Session,
    company_id: int,
    category: Optional[TechCategory] = None,
) -> List[CompanyTechORM]:
    """Get company tech stack, optionally filtered by category"""
    query = db.query(CompanyTechORM).filter(CompanyTechORM.company_id == company_id)
    
    if category:
        query = query.filter(CompanyTechORM.category == category)
    
    return query.order_by(CompanyTechORM.detected_at.desc()).all()


def get_company_intent_signals(
    db: Session,
    company_id: int,
    type: Optional[IntentSignalType] = None,
    strength: Optional[IntentStrength] = None,
    active_only: bool = True,
) -> List[CompanyIntentORM]:
    """Get company intent signals, optionally filtered"""
    query = db.query(CompanyIntentORM).filter(CompanyIntentORM.company_id == company_id)
    
    if type:
        query = query.filter(CompanyIntentORM.type == type)
    
    if strength:
        query = query.filter(CompanyIntentORM.strength == strength)
    
    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            or_(
                CompanyIntentORM.expires_at.is_(None),
                CompanyIntentORM.expires_at > now
            )
        )
    
    return query.order_by(CompanyIntentORM.detected_at.desc()).all()


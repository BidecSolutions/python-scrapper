"""Tech Stack & Intent Enrichment ORM models"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, Float, func, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base


class TechCategory(str, enum.Enum):
    crm = "crm"
    marketing = "marketing"
    sales_engagement = "sales_engagement"
    billing = "billing"
    ecommerce = "ecommerce"
    infrastructure = "infrastructure"
    analytics = "analytics"
    security = "security"
    other = "other"


class IntentSignalType(str, enum.Enum):
    hiring = "hiring"
    tech_change = "tech_change"
    content = "content"
    keyword = "keyword"
    funding = "funding"
    expansion = "expansion"
    other = "other"


class IntentStrength(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class CompanyTechORM(Base):
    """Company technology stack"""
    __tablename__ = "company_tech"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    product_name = Column(String(255), nullable=False, index=True)  # "HubSpot", "Salesforce"
    category = Column(Enum(TechCategory), nullable=False, index=True)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)  # 0.0 - 1.0
    
    # Source of detection
    source = Column(String(50), nullable=True)  # "builtwith", "internal", "wappalyzer", etc.
    
    # Optional: version, features detected
    version = Column(String(50), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data (renamed from metadata - reserved in SQLAlchemy)
    
    # Relationships
    company = relationship("CompanyORM", back_populates="tech_stack")
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_company_tech_company", "company_id"),
        Index("idx_company_tech_category", "category"),
        Index("idx_company_tech_product", "product_name"),
        Index("idx_company_tech_org", "organization_id"),
    )


class CompanyIntentORM(Base):
    """Company buying intent signals"""
    __tablename__ = "company_intent"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(Enum(IntentSignalType), nullable=False, index=True)
    strength = Column(Enum(IntentStrength), nullable=False, default=IntentStrength.low, index=True)
    
    description = Column(String(500), nullable=True)  # "Hiring SDRs", "Visited pricing page"
    source = Column(String(50), nullable=True)  # "jobs_api", "web_analytics", "provider_x"
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Signals decay over time
    
    # Optional extra data
    extra_data = Column(Text, nullable=True)  # JSON string for additional data (renamed from metadata - reserved in SQLAlchemy)
    
    # Relationships
    company = relationship("CompanyORM", back_populates="intent_signals")
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_company_intent_company", "company_id"),
        Index("idx_company_intent_type", "type"),
        Index("idx_company_intent_strength", "strength"),
        Index("idx_company_intent_detected", "detected_at"),
        Index("idx_company_intent_org", "organization_id"),
    )


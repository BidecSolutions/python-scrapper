"""Company ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey, 
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base


class CompanyORM(Base):
    """Company database model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    
    # Company details
    size = Column(String(50), nullable=True)  # "11-50", "51-200", etc.
    industry = Column(String(100), nullable=True, index=True)
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    
    # Additional metadata
    description = Column(String(1000), nullable=True)
    website = Column(String(512), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    
    # Relationships
    leads = relationship("LeadORM", back_populates="company", cascade="all, delete-orphan")
    tech_stack = relationship("CompanyTechORM", back_populates="company", cascade="all, delete-orphan")
    intent_signals = relationship("CompanyIntentORM", back_populates="company", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_company_domain", "domain"),
        Index("idx_company_name", "name"),
    )


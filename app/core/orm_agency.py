"""Agency / White-Label ORM models"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base


class AgencyRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class AgencyORM(Base):
    """Agency model for white-label / multi-tenant"""
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    
    # White-label / branding
    logo_url = Column(String(512), nullable=True)
    primary_color = Column(String(20), nullable=True)  # "#0052CC" etc.
    subdomain = Column(String(255), nullable=True, unique=True, index=True)  # "myagency" -> myagency.yourapp.com
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    
    # Settings
    hide_powered_by = Column(Boolean, nullable=False, default=False)  # Hide "Powered by Bidec"
    custom_domain = Column(String(255), nullable=True)  # For future: full custom domain
    
    # Metadata
    settings = Column(Text, nullable=True)  # JSON string for additional config
    
    # Relationships
    organization = relationship("app.core.orm.OrganizationORM")
    members = relationship("AgencyMemberORM", back_populates="agency", cascade="all, delete-orphan")
    client_workspaces = relationship("app.core.orm_workspaces.WorkspaceORM", back_populates="agency", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_agency_org", "organization_id"),
        Index("idx_agency_subdomain", "subdomain"),
    )


class AgencyMemberORM(Base):
    """Agency members (users who can access agency's client workspaces)"""
    __tablename__ = "agency_members"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(Enum(AgencyRole), nullable=False, default=AgencyRole.member, index=True)
    
    # Relationships
    agency = relationship("AgencyORM", back_populates="members")
    user = relationship("app.core.orm.UserORM", back_populates="agency_memberships")
    
    __table_args__ = (
        UniqueConstraint("agency_id", "user_id", name="uq_agency_user"),
        Index("idx_agency_member_agency", "agency_id"),
        Index("idx_agency_member_user", "user_id"),
    )


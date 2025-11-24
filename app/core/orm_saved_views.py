"""Saved Views ORM - For user/org saved filter views"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class SavedViewORM(Base):
    """Saved filter view for Leads, Jobs, Deals, Verification pages"""
    __tablename__ = "saved_views"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # null = org-wide view
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

    # View metadata
    name = Column(String(255), nullable=False)
    page_type = Column(String(50), nullable=False, index=True)  # "leads", "jobs", "deals", "verification"
    is_pinned = Column(Boolean, nullable=False, default=False, index=True)
    is_shared = Column(Boolean, nullable=False, default=False)  # true = org-wide, false = personal

    # Filter & sort configuration (stored as JSON)
    filters = Column(JSON, nullable=False, default=dict)  # { search: "...", source: "...", quality: "high", etc. }
    sort_by = Column(String(50), nullable=True)  # "created_at", "score", "name", etc.
    sort_order = Column(String(10), nullable=True, default="desc")  # "asc" or "desc"

    # Optional: column visibility preferences
    visible_columns = Column(JSON, nullable=True)  # ["name", "email", "score", ...] or null = default

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    usage_count = Column(Integer, nullable=False, default=0)

    # Relationships
    organization = relationship("OrganizationORM", back_populates="saved_views")
    user = relationship("UserORM", back_populates="saved_views")
    workspace = relationship("WorkspaceORM", back_populates="saved_views")

    __table_args__ = (
        Index("idx_saved_views_org_page_pinned", "organization_id", "page_type", "is_pinned"),
        Index("idx_saved_views_user_page", "user_id", "page_type"),
    )


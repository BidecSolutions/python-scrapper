"""Email sync and tracking ORM models"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, func, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db import Base


class EmailDirection(str, enum.Enum):
    outbound = "outbound"
    inbound = "inbound"


class EmailMessageORM(Base):
    """Email message log for tracking outbound and inbound emails"""
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    direction = Column(Enum(EmailDirection), nullable=False, index=True)  # outbound/inbound
    
    # Email headers
    message_id = Column(String(255), nullable=True, index=True)  # Message-ID header
    in_reply_to = Column(String(255), nullable=True, index=True)  # In-Reply-To header
    references = Column(Text, nullable=True)  # References header
    
    subject = Column(String(500), nullable=True)
    from_email = Column(String(255), nullable=False, index=True)
    to_email = Column(String(255), nullable=False, index=True)
    cc_email = Column(String(500), nullable=True)
    bcc_email = Column(String(500), nullable=True)
    
    # Links to campaigns and leads
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Raw data
    raw_headers = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    snippet = Column(String(2000), nullable=True)  # First 2000 chars for quick preview
    
    # Classification
    is_bounce = Column(Boolean, nullable=False, default=False, index=True)
    is_unsubscribe = Column(Boolean, nullable=False, default=False, index=True)
    is_reply = Column(Boolean, nullable=False, default=False, index=True)
    is_ooo = Column(Boolean, nullable=False, default=False, index=True)  # Out of office
    
    # Processing status
    processed = Column(Boolean, nullable=False, default=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Relationships
    workspace = relationship("WorkspaceORM")
    organization = relationship("OrganizationORM")
    campaign = relationship("CampaignORM")
    lead = relationship("LeadORM")
    
    __table_args__ = (
        Index("idx_email_message_id", "message_id"),
        Index("idx_email_in_reply_to", "in_reply_to"),
        Index("idx_email_workspace_created", "workspace_id", "created_at"),
        Index("idx_email_lead_created", "lead_id", "created_at"),
    )


class EmailSyncConfigORM(Base):
    """Configuration for email sync (BCC address, IMAP settings, etc.)"""
    __tablename__ = "email_sync_configs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # BCC tracking address
    bcc_email = Column(String(255), nullable=True, unique=True, index=True)  # e.g., reply+workspace_id@domain.com
    
    # IMAP/API settings (for future direct integration)
    sync_type = Column(String(50), nullable=False, default="bcc")  # "bcc", "gmail_api", "outlook_api"
    imap_host = Column(String(255), nullable=True)
    imap_port = Column(Integer, nullable=True)
    imap_username = Column(String(255), nullable=True)
    imap_password = Column(String(255), nullable=True)  # Encrypted in production
    imap_folder = Column(String(255), nullable=True, default="INBOX")
    
    # OAuth tokens (for Gmail/Outlook API)
    oauth_access_token = Column(Text, nullable=True)  # Encrypted
    oauth_refresh_token = Column(Text, nullable=True)  # Encrypted
    oauth_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Sync status
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_error = Column(Text, nullable=True)
    
    # Settings
    settings = Column(Text, nullable=True)  # JSON string for additional config
    
    # Relationships
    workspace = relationship("WorkspaceORM")
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_email_sync_workspace", "workspace_id"),
    )


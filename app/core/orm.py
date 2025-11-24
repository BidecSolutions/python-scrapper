"""SQLAlchemy ORM models - Comprehensive schema for B2B SaaS"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Enum as SQLEnum, Text, Numeric, Index, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY  # JSONB for PostgreSQL
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import uuid

from app.core.db import Base

# Import APIKeyORM from separate module to avoid duplicate class definitions
# This import must be done after Base is defined but relationships can use string references
try:
    from app.core.orm_api_keys import APIKeyORM as _APIKeyORM
except ImportError:
    _APIKeyORM = None

# Use JSONB for PostgreSQL, JSON for SQLite (compatible type)
# Use ARRAY for PostgreSQL, JSON for SQLite (arrays stored as JSON arrays)
# Check database URL to determine which type to use
from app.core.config import settings
if settings.DATABASE_URL.startswith("postgresql"):
    JsonType = JSONB  # PostgreSQL supports JSONB
    ArrayType = ARRAY  # PostgreSQL supports ARRAY
else:
    JsonType = JSON  # SQLite uses JSON
    ArrayType = JSON  # SQLite stores arrays as JSON


# ============================================================================
# Enumerations
# ============================================================================

class JobStatus(str, PyEnum):
    """Job status enumeration"""
    pending = "pending"
    running = "running"
    ai_pending = "ai_pending"  # Waiting for AI processing
    completed = "completed"
    failed = "failed"
    completed_with_warnings = "completed_with_warnings"


class LeadStatus(str, PyEnum):
    """Lead status for workflow"""
    new = "new"
    assigned = "assigned"
    contacted = "contacted"
    interested = "interested"
    follow_up = "follow_up"
    closed_won = "closed_won"
    closed_lost = "closed_lost"


class UserRole(str, PyEnum):
    """User roles within an organization"""
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class UserStatus(str, PyEnum):
    """User account status"""
    pending = "pending"      # signed up but not approved
    active = "active"        # can use app
    suspended = "suspended"  # blocked


class PlanTier(str, PyEnum):
    """Subscription plan tiers"""
    free = "free"
    starter = "starter"
    pro = "pro"
    agency = "agency"
    enterprise = "enterprise"


class APIKeyStatus(str, PyEnum):
    """API key status"""
    active = "active"
    revoked = "revoked"


# ============================================================================
# Multi-tenant: Organizations & Users
# ============================================================================

class OrganizationORM(Base):
    """Organization model (multi-tenant)"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    plan_tier = Column(SQLEnum(PlanTier), nullable=False, default=PlanTier.free, index=True)
    logo_url = Column(String(512), nullable=True)  # URL or path to organization logo
    brand_name = Column(String(255), nullable=True)  # Custom brand/display name (e.g., "LeadFlux AI")
    tagline = Column(String(255), nullable=True)  # Custom tagline (e.g., "Scrape • Enrich • Score")
    
    # Credits & Billing
    credits_balance = Column(Integer, nullable=False, default=0)
    credits_limit = Column(Integer, nullable=False, default=1000)  # Monthly limit
    credits_reset_at = Column(DateTime(timezone=True), nullable=True)  # Next reset date
    
    # Settings
    settings = Column(JsonType, nullable=False, default=dict)  # IP allowlist, legal notes, etc.
    
    # Relationships
    users = relationship("UserORM", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("app.core.orm_api_keys.APIKeyORM", back_populates="organization", cascade="all, delete-orphan")
    jobs = relationship("ScrapeJobORM", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("LeadORM", back_populates="organization", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecordORM", back_populates="organization", cascade="all, delete-orphan")
    lead_lists = relationship("LeadListORM", back_populates="organization", cascade="all, delete-orphan")
    saved_views = relationship("app.core.orm_saved_views.SavedViewORM", back_populates="organization", cascade="all, delete-orphan")
    duplicate_groups = relationship("app.core.orm_duplicates.DuplicateGroupORM", back_populates="organization", cascade="all, delete-orphan")


class UserORM(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    full_name = Column(String(255), nullable=True)
    
    # Account status (platform-level)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.pending, index=True)
    
    # Platform-level permissions
    is_super_admin = Column(Boolean, nullable=False, default=False, index=True)
    can_use_advanced = Column(Boolean, nullable=False, default=False, index=True)
    
    # Multi-tenant (workspace-based)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)  # Made nullable for signup flow
    current_workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)  # Current active workspace
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.member, index=True)
    
    # Legacy status (keep for backward compatibility, but use status field instead)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM", back_populates="users", foreign_keys=[organization_id])
    current_workspace = relationship("WorkspaceORM", foreign_keys=[current_workspace_id])
    assigned_leads = relationship("LeadORM", foreign_keys="LeadORM.assigned_to_user_id", back_populates="assigned_to")
    owned_leads = relationship("LeadORM", foreign_keys="LeadORM.owner_user_id", back_populates="owner")
    lead_comments = relationship("LeadCommentORM", back_populates="user")
    activity_logs = relationship("ActivityLogORM", back_populates="user")
    workspaces = relationship(
        "WorkspaceMemberORM", 
        back_populates="user", 
        cascade="all, delete-orphan",
        primaryjoin="UserORM.id == WorkspaceMemberORM.user_id"
    )
    agency_memberships = relationship("app.core.orm_agency.AgencyMemberORM", back_populates="user", cascade="all, delete-orphan")
    saved_views = relationship("app.core.orm_saved_views.SavedViewORM", back_populates="user", cascade="all, delete-orphan")


# ============================================================================
# API Keys - Moved to app.core.orm_api_keys
# ============================================================================
# APIKeyORM is now defined in app/core/orm_api_keys.py to support workspace-scoped keys
# For backward compatibility, relationships reference it by string name


# ============================================================================
# Plans & Usage Tracking
# ============================================================================

class UsageRecordORM(Base):
    """Usage tracking for quota enforcement"""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Usage type
    usage_type = Column(String(50), nullable=False, index=True)  # "leads_scraped", "api_calls", "jobs_run"
    quantity = Column(Integer, nullable=False, default=1)  # Number of units used
    
    # Context
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="SET NULL"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    meta = Column(JsonType, nullable=False, default=dict)  # Renamed from metadata (SQLAlchemy reserved)
    
    # AI-generated personalization
    intro_line = Column(Text, nullable=True)  # AI-generated first line for outreach
    intro_line_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # CRM integration
    hubspot_contact_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    organization = relationship("OrganizationORM", back_populates="usage_records")
    api_key = relationship("app.core.orm_api_keys.APIKeyORM", back_populates="usage_records")
    # Import and reference directly to avoid SQLAlchemy conflicts
    
    # Index for monthly aggregation
    __table_args__ = (
        Index("idx_usage_org_type_created", "organization_id", "usage_type", "created_at"),
    )


# ============================================================================
# Jobs & Leads (Enhanced)
# ============================================================================

class ScrapeJobORM(Base):
    """Scrape job database model (enhanced)"""
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Job parameters
    niche = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True, index=True)
    max_results = Column(Integer, nullable=False)
    max_pages_per_site = Column(Integer, nullable=False)
    
    # Status & results
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.pending, index=True)
    error_message = Column(Text, nullable=True)
    result_count = Column(Integer, nullable=False, default=0)
    
    # Analytics
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Progress tracking
    total_targets = Column(Integer, nullable=True)  # Total sites we plan to process
    processed_targets = Column(Integer, nullable=False, default=0)  # Sites already processed
    
    # Extraction configuration
    extract_config = Column(JsonType, nullable=False, default=dict)  # What data to extract
    
    # Performance metrics
    sites_crawled = Column(Integer, nullable=False, default=0)
    sites_failed = Column(Integer, nullable=False, default=0)
    total_pages_crawled = Column(Integer, nullable=False, default=0)
    sources_used = Column(ArrayType(String), nullable=True)  # ["google_places", "web_search"]
    
    # Relationships
    organization = relationship("OrganizationORM", back_populates="jobs")
    leads = relationship("LeadORM", back_populates="job", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecordORM")
    segments = relationship("JobSegmentORM", back_populates="job", cascade="all, delete-orphan")
    insights = relationship("JobInsightORM", back_populates="job", uselist=False, cascade="all, delete-orphan")
    # workflow relationship removed - add workflow_id foreign key column first if needed


class LeadORM(Base):
    """Lead database model (comprehensive)"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)  # Workspace for team collaboration
    
    # Basic info
    name = Column(String(255), nullable=True, index=True)
    niche = Column(String(255), index=True, nullable=True)
    website = Column(String(500), index=True, nullable=True)
    emails = Column(JsonType, nullable=False, default=list)  # ["a@x.com", "b@y.com"]
    phones = Column(JsonType, nullable=False, default=list)  # ["+92...", "03xx..."]
    address = Column(Text, nullable=True)
    source = Column(String(100), nullable=False, index=True)  # Primary source (for backward compatibility)
    sources = Column(ArrayType(String), nullable=True)  # All sources this lead came from ["google_search", "yellowpages"]
    source_robot_run_id = Column(Integer, ForeignKey("robot_runs.id", ondelete="SET NULL"), nullable=True, index=True)  # If imported from robot
    company_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)  # Link to identity graph
    city = Column(String(255), index=True, nullable=True)
    country = Column(String(100), index=True, nullable=True)
    
    # Next Best Action fields
    nb_action = Column(String(32), nullable=True, index=True)  # Next best action type
    nb_action_score = Column(Numeric(5, 2), nullable=True)  # Action confidence score
    nb_action_generated_at = Column(DateTime(timezone=True), nullable=True)  # When action was generated
    
    # Job reference
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    is_new_since_last_job = Column(Boolean, nullable=False, default=True)  # Delta detection
    
    # ========== NEW ENRICHMENT FIELDS ==========
    
    # Tech stack detection
    cms = Column(String(100), nullable=True, index=True)  # "wordpress", "wix", "shopify"
    tech_stack = Column(ArrayType(String), nullable=True)  # ["react", "bootstrap", "stripe"]
    third_party_widgets = Column(ArrayType(String), nullable=True)  # ["calendly", "hotjar", "intercom"]
    
    # Social links
    social_links = Column(JsonType, nullable=False, default=dict)  # {"facebook": "url", "instagram": "url", ...}
    
    # Company intelligence
    company_size = Column(String(50), nullable=True, index=True)  # "solo", "small", "medium", "large"
    revenue_band = Column(String(50), nullable=True)  # "micro", "small", "large"
    is_multi_location = Column(Boolean, nullable=False, default=False)
    branch_locations = Column(ArrayType(String), nullable=True)  # ["City1", "City2"]
    organization_id_dedup = Column(Integer, nullable=True)  # Links related leads to same org
    
    # Content-based tags
    service_tags = Column(ArrayType(String), nullable=True, index=True)  # ["dermatology", "cardiology"]
    audience_tags = Column(ArrayType(String), nullable=True)  # ["kids", "families", "corporate"]
    
    # Contact person (for outreach)
    contact_person_name = Column(String(255), nullable=True)
    
    # Lead ownership (for rep performance tracking)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Primary rep/owner of this lead
    contact_person_role = Column(String(255), nullable=True)
    contact_person_email = Column(String(255), nullable=True)
    
    # Outreach notes
    outreach_notes = Column(Text, nullable=True)  # Auto-generated personalization notes
    
    # ========== WORKFLOW FIELDS ==========
    
    # Status & assignment
    status = Column(SQLEnum(LeadStatus), nullable=False, default=LeadStatus.new, index=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Quality & scoring
    quality_score = Column(Numeric(5, 2), nullable=True)  # 0-100 (rule-based)
    quality_label = Column(String(20), nullable=True, index=True)  # "low", "medium", "high"
    smart_score = Column(Numeric(5, 2), nullable=True)  # 0-1 ML probability score
    smart_score_version = Column(Integer, nullable=True)  # Model version used
    fit_label = Column(String(20), nullable=True, index=True)  # "good", "bad", "won" (from feedback)
    has_email = Column(Boolean, nullable=False, default=False, index=True)
    has_phone = Column(Boolean, nullable=False, default=False, index=True)
    has_social = Column(Boolean, nullable=False, default=False, index=True)
    
    # Lead Health Score (new)
    health_score = Column(Numeric(5, 2), nullable=True, index=True)  # 0-100, computed from deliverability + fit + engagement + source
    health_score_last_calculated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Next Best Action (NBA)
    next_action = Column(String(50), nullable=True, index=True)  # "add_to_campaign", "schedule_follow_up", "nurture_only", "review_or_enrich", "drop_or_suspend"
    next_action_reason = Column(Text, nullable=True)  # Human-readable reason
    next_action_last_calculated_at = Column(DateTime(timezone=True), nullable=True)
    
    # AI Segments
    segment_id = Column(Integer, ForeignKey("job_segments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Metadata (renamed to meta - SQLAlchemy reserved word)
    meta = Column(JsonType, nullable=False, default=dict)  # Flexible storage for future fields
    custom_fields = Column(JsonType, nullable=True)  # User-defined custom fields extracted by AI
    
    # Tech stack & digital maturity
    tech_stack = Column(JsonType, nullable=False, default=dict)  # {"cms": "WordPress", "tools": ["GA", "Chat"]}
    digital_maturity = Column(Numeric(5, 2), nullable=True)  # 0-100 score
    
    # QA / Anomaly detection
    qa_status = Column(String(20), nullable=True, default="unknown", index=True)  # "ok", "review", "bad"
    qa_reason = Column(Text, nullable=True)  # AI explanation for QA status
    
    # Embeddings for similarity search (stored as JSON array for SQLite compatibility)
    embedding = Column(JsonType, nullable=True)  # Vector embedding for lookalike finder
    
    # ========== AI-SPECIFIC FIELDS ==========
    
    # Language detection
    language = Column(String(10), nullable=True, index=True)  # "en", "ur", "ar", etc.
    
    # Tags (general-purpose tags for filtering)
    tags = Column(JsonType, nullable=False, default=list)  # ["24_7", "online_booking", "premium", ...]
    
    # AI quality label
    quality_label = Column(String(50), nullable=True, index=True)  # "low", "medium", "high"
    
    # Clustering
    cluster_id = Column(Integer, nullable=True, index=True)  # For market segmentation
    
    # AI processing status
    ai_status = Column(String(50), nullable=True, index=True)  # "pending", "success", "failed"
    ai_last_error = Column(Text, nullable=True)  # Error message if AI processing failed
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)  # When AI enrichment completed
    
    # Relationships
    organization = relationship("OrganizationORM", back_populates="leads")
    workspace = relationship("WorkspaceORM", foreign_keys=[workspace_id])  # Workspace relationship
    job = relationship("ScrapeJobORM", back_populates="leads")
    company = relationship("CompanyORM", foreign_keys=[company_id], back_populates="leads")
    assigned_to = relationship("UserORM", foreign_keys=[assigned_to_user_id], back_populates="assigned_leads")
    owner = relationship("UserORM", foreign_keys=[owner_user_id], back_populates="owned_leads")
    comments = relationship("LeadCommentORM", back_populates="lead", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLogORM", back_populates="lead")
    notes = relationship("LeadNoteORM", back_populates="lead", cascade="all, delete-orphan")
    tasks = relationship("LeadTaskORM", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("ActivityORM", back_populates="lead", cascade="all, delete-orphan")
    snapshots = relationship("LeadSnapshotORM", back_populates="lead", cascade="all, delete-orphan")
    feedback = relationship("LeadFeedbackORM", back_populates="lead", cascade="all, delete-orphan")
    segment = relationship("JobSegmentORM", back_populates="leads")
    # V2 relationships removed - defined in orm_v2.py models instead to avoid import issues
    source_robot_run = relationship("RobotRunORM", back_populates="imported_leads")  # Robot import relationship
    email_records = relationship("EmailORM", back_populates="lead", cascade="all, delete-orphan")
    list_memberships = relationship("app.core.orm_lists.LeadListLeadORM", back_populates="lead", cascade="all, delete-orphan")  # List memberships
    duplicate_entries = relationship("app.core.orm_duplicates.DuplicateLeadORM", back_populates="lead", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_lead_org_status", "organization_id", "status"),
        Index("idx_lead_org_assigned", "organization_id", "assigned_to_user_id"),
        Index("idx_lead_website_org", "website", "organization_id"),
        Index("idx_lead_quality_score", "quality_score"),
        Index("idx_lead_quality_label", "quality_label"),
        Index("idx_lead_ai_status", "ai_status"),
        Index("idx_lead_tags", "tags", postgresql_using="gin"),  # GIN index for JsonType array queries
    )


# ============================================================================
# Collaboration & Workflow
# ============================================================================

class LeadCommentORM(Base):
    """Comments on leads for team collaboration"""
    __tablename__ = "lead_comments"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    content = Column(Text, nullable=False)
    mentions = Column(ArrayType(Integer), nullable=True)  # User IDs mentioned with @username
    
    # Relationships
    lead = relationship("LeadORM", back_populates="comments")
    user = relationship("UserORM", back_populates="lead_comments")


class ActivityLogORM(Base):
    """Activity timeline for leads and jobs"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # What this activity is about
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)  # "lead.created", "lead.assigned", "status.changed"
    description = Column(Text, nullable=False)
    meta = Column(JsonType, nullable=False, default=dict)  # Additional context (renamed from metadata - SQLAlchemy reserved)
    
    # Relationships
    lead = relationship("LeadORM", back_populates="activity_logs")
    job = relationship("ScrapeJobORM")
    user = relationship("UserORM", back_populates="activity_logs")
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_activity_org_created", "organization_id", "created_at"),
    )


# ============================================================================
# Saved Queries / Views
# ============================================================================

class SavedQueryORM(Base):
    """Saved search queries/views"""
    __tablename__ = "saved_queries"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Query parameters (JsonType for flexibility)
    filters = Column(JsonType, nullable=False, default=dict)  # {"has_email": true, "city": "Karachi", ...}
    sort_by = Column(String(100), nullable=True)
    sort_order = Column(String(10), nullable=True, default="desc")
    
    # Relationships
    organization = relationship("OrganizationORM")


# ============================================================================
# Webhooks
# ============================================================================

class WebhookORM(Base):
    """Webhook configuration for integrations"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)  # For HMAC signature
    events = Column(ArrayType(String), nullable=False)  # ["lead.created", "job.completed"]
    
    is_active = Column(Boolean, nullable=False, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    organization = relationship("OrganizationORM")


# ============================================================================
# AI & ML: Lead Snapshots for AI Processing
# ============================================================================

class LeadSnapshotORM(Base):
    """Raw text snapshots of website pages for AI processing"""
    __tablename__ = "lead_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Page details
    page_type = Column(String(50), nullable=False, index=True)  # "home", "contact", "about"
    url = Column(String(500), nullable=False)
    
    # Content
    text = Column(Text, nullable=False)  # Cleaned text content
    html_hash = Column(String(64), nullable=True)  # SHA256 hash of HTML for deduplication
    
    # Relationships
    lead = relationship("LeadORM", back_populates="snapshots")
    
    __table_args__ = (
        Index("idx_snapshot_lead_type", "lead_id", "page_type"),
    )


# ============================================================================
# AI & ML: Embeddings for Clustering & Semantic Search
# ============================================================================

class LeadEmbeddingORM(Base):
    """Embeddings for leads (for clustering and semantic search)"""
    __tablename__ = "lead_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Embedding details
    model = Column(String(100), nullable=False)  # "sentence-transformers/all-MiniLM-L6-v2"
    dim = Column(Integer, nullable=False)  # Dimension of embedding vector
    vector = Column(ArrayType(Numeric), nullable=False)  # Embedding vector (PostgreSQL array)
    
    # Relationships
    lead = relationship("LeadORM")
    
    __table_args__ = (
        Index("idx_embedding_lead", "lead_id"),
    )


# ============================================================================
# AI & ML: Smart Scoring & Feedback
# ============================================================================

class LeadFeedbackORM(Base):
    """User feedback on leads for ML training"""
    __tablename__ = "lead_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    label = Column(String(20), nullable=False, index=True)  # "good", "bad", "won"
    
    # Relationships
    organization = relationship("OrganizationORM")
    lead = relationship("LeadORM")
    user = relationship("UserORM")
    
    __table_args__ = (
        Index("idx_feedback_org_lead", "organization_id", "lead_id"),
    )


class OrgModelORM(Base):
    """Trained ML models per organization"""
    __tablename__ = "org_models"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # "lead_scoring"
    version = Column(Integer, nullable=False)
    trained_at = Column(DateTime(timezone=True), nullable=False)
    
    # Model storage (for v1, store path to file; later could store in DB)
    model_path = Column(String(500), nullable=True)  # Path to .pkl file
    params = Column(JsonType, nullable=False, default=dict)  # Model hyperparameters
    metrics = Column(JsonType, nullable=False, default=dict)  # {"auc": 0.87, "accuracy": 0.78}
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "type", "version", name="uq_org_model_version"),
        Index("idx_model_org_type", "organization_id", "type"),
    )


# ============================================================================
# AI & ML: Segments & Insights
# ============================================================================

class JobSegmentORM(Base):
    """AI-generated segments for jobs"""
    __tablename__ = "job_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    cluster_index = Column(Integer, nullable=False)  # Index from k-means or similar
    
    label = Column(String(100), nullable=False)  # "Premium private hospitals"
    description = Column(Text, nullable=False)  # LLM-generated description
    
    # Relationships
    job = relationship("ScrapeJobORM")
    leads = relationship("LeadORM", back_populates="segment")
    
    __table_args__ = (
        Index("idx_segment_job", "job_id"),
    )


class JobInsightORM(Base):
    """LLM-generated market insights for jobs"""
    __tablename__ = "job_insights"
    
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="CASCADE"), primary_key=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    text = Column(Text, nullable=False)  # LLM-generated insights text
    stats = Column(JsonType, nullable=False, default=dict)  # Computed statistics
    
    # Relationships
    job = relationship("ScrapeJobORM")


# ============================================================================
# Custom Fields
# ============================================================================

class CustomFieldORM(Base):
    """Custom field definitions per organization"""
    __tablename__ = "custom_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(64), nullable=False)  # Internal key: 'has_parking'
    label = Column(String(128), nullable=False)  # Display label: 'Has parking'
    type = Column(String(20), nullable=False)  # 'bool', 'text', 'list', 'number'
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_field_name"),
        Index("idx_custom_field_org_active", "organization_id", "active"),
    )


# ============================================================================
# AI Playbooks
# ============================================================================

class PlaybookORM(Base):
    """AI-generated market playbooks per niche+location"""
    __tablename__ = "playbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    niche = Column(String(128), nullable=False, index=True)
    location = Column(String(128), nullable=False, index=True)
    
    text = Column(Text, nullable=False)  # Markdown playbook content
    stats = Column(JsonType, nullable=False, default=dict)  # Aggregated stats
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "niche", "location", name="uq_playbook_niche_location"),
        Index("idx_playbook_org_niche", "organization_id", "niche"),
    )


# ============================================================================
# Email Finder & Verifier
# ============================================================================

class EmailVerificationStatus(str, PyEnum):
    """Email verification status"""
    valid = "valid"
    invalid = "invalid"
    risky = "risky"
    unknown = "unknown"
    disposable = "disposable"
    gibberish = "gibberish"


class EmailVerificationORM(Base):
    """Cache for email verification results"""
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Email
    email = Column(String(255), nullable=False, index=True)
    
    # Verification result
    status = Column(SQLEnum(EmailVerificationStatus), nullable=False, index=True)
    reason = Column(String(100), nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)  # 0.0-1.0
    
    # Metadata
    mx_records = Column(ArrayType(String), nullable=True)  # MX hosts checked
    smtp_checked = Column(Boolean, nullable=False, default=False)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_email_verification"),
        Index("idx_email_verification_status", "organization_id", "status"),
    )


# ============================================================================
# Email Finder & Verifier Jobs
# ============================================================================

class EmailFinderJobStatus(str, PyEnum):
    """Email finder job status"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class EmailVerificationJobStatus(str, PyEnum):
    """Email verification job status"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class EmailFinderJobORM(Base):
    """Email finder job for bulk email finding"""
    __tablename__ = "email_finder_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Job metadata
    name = Column(String(255), nullable=True)
    status = Column(SQLEnum(EmailFinderJobStatus), nullable=False, default=EmailFinderJobStatus.pending, index=True)
    error_message = Column(Text, nullable=True)
    
    # Input data
    input_data = Column(JsonType, nullable=False, default=list)  # Array of {first_name, last_name, company, domain}
    total_inputs = Column(Integer, nullable=False, default=0)
    
    # Progress tracking
    processed_count = Column(Integer, nullable=False, default=0)
    found_count = Column(Integer, nullable=False, default=0)
    not_found_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    
    # Settings
    skip_smtp = Column(Boolean, nullable=False, default=False)
    min_confidence = Column(Numeric(3, 2), nullable=False, default=0.3)
    auto_save_to_leads = Column(Boolean, nullable=False, default=False)
    target_list_id = Column(Integer, nullable=True)  # Future: link to lead_lists table
    
    # Results (summary)
    results = Column(JsonType, nullable=True)  # Array of find results
    
    # Credits
    credits_used = Column(Integer, nullable=False, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_email_finder_jobs_org", "organization_id"),
        Index("idx_email_finder_jobs_status", "status"),
        Index("idx_email_finder_jobs_created", "created_at"),
    )


class EmailVerificationJobORM(Base):
    """Email verification job for bulk verification"""
    __tablename__ = "email_verification_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Job metadata
    source_type = Column(String(20), nullable=False, default="leads")  # 'leads', 'csv'
    source_description = Column(Text, nullable=True)  # "Selected 523 leads" or file name
    status = Column(SQLEnum(EmailVerificationJobStatus), nullable=False, default=EmailVerificationJobStatus.pending, index=True)
    error_message = Column(Text, nullable=True)
    
    # Input: List of emails (for CSV jobs)
    input_emails = Column(ArrayType(String), nullable=True)  # Only for CSV jobs
    total_emails = Column(Integer, nullable=False, default=0)
    
    # Progress tracking
    processed_count = Column(Integer, nullable=False, default=0)
    valid_count = Column(Integer, nullable=False, default=0)
    invalid_count = Column(Integer, nullable=False, default=0)
    risky_count = Column(Integer, nullable=False, default=0)
    unknown_count = Column(Integer, nullable=False, default=0)
    disposable_count = Column(Integer, nullable=False, default=0)
    syntax_error_count = Column(Integer, nullable=False, default=0)
    
    # Settings
    skip_smtp = Column(Boolean, nullable=False, default=False)
    
    # Credits
    credits_used = Column(Integer, nullable=False, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    items = relationship("EmailVerificationItemORM", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_email_verification_jobs_org", "organization_id"),
        Index("idx_email_verification_jobs_status", "status"),
    )


class EmailFinderResultORM(Base):
    """Individual email finder result"""
    __tablename__ = "email_finder_results"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("email_finder_jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Input
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    
    # Output
    found_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)  # found, not_found, error
    confidence = Column(Numeric(3, 2), nullable=True)
    verification_status = Column(String(50), nullable=True)  # valid, invalid, risky, unknown
    verification_reason = Column(String(100), nullable=True)
    
    # Metadata
    candidates_checked = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    
    # Link to lead (if auto-saved)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    job = relationship("EmailFinderJobORM")
    lead = relationship("LeadORM")
    
    __table_args__ = (
        Index("idx_email_finder_results_org", "organization_id"),
        Index("idx_email_finder_results_job", "job_id"),
        Index("idx_email_finder_results_domain", "domain"),
    )


# ============================================================================
# Credits & Billing
# ============================================================================

class CreditTransactionType(str, PyEnum):
    """Credit transaction types"""
    deduction = "deduction"
    grant = "grant"
    reset = "reset"


class CreditTransactionORM(Base):
    """Credit transaction history"""
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(SQLEnum(CreditTransactionType), nullable=False)
    amount = Column(Integer, nullable=False)  # Positive for grants, negative for deductions
    balance_after = Column(Integer, nullable=False)
    
    # Context
    feature = Column(String(50), nullable=True)  # 'email_finder', 'email_verifier', 'scraping_job', 'robot_run'
    reference_id = Column(Integer, nullable=True)  # Job ID, etc.
    reference_type = Column(String(50), nullable=True)  # 'email_finder_job', 'verification_job', etc.
    
    description = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        Index("idx_credit_transactions_org", "organization_id"),
        Index("idx_credit_transactions_created", "created_at"),
    )


# ============================================================================
# Canonical Email Records
# ============================================================================

class EmailORM(Base):
    """Canonical email records (separate from leads for verification/finder)"""
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Email
    email = Column(String(255), nullable=False, index=True)
    label = Column(String(50), nullable=True)  # 'primary', 'secondary', 'billing', etc.
    
    # Verification state
    verify_status = Column(String(20), nullable=True, index=True)  # 'valid', 'invalid', 'risky', 'unknown', 'disposable', 'syntax_error'
    verify_reason = Column(Text, nullable=True)
    verify_confidence = Column(Numeric(3, 2), nullable=True)  # 0.0-1.0
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Finder info
    found_via = Column(String(20), nullable=True)  # 'scrape', 'finder', 'import', 'manual'
    finder_job_id = Column(Integer, ForeignKey("email_finder_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    lead = relationship("LeadORM", back_populates="email_records")
    finder_job = relationship("EmailFinderJobORM")
    
    __table_args__ = (
        Index("idx_emails_org_lead", "organization_id", "lead_id"),
        Index("idx_emails_email", "email"),
        Index("idx_emails_verify_status", "organization_id", "verify_status"),
    )


# ============================================================================
# Email Verification Items (per-email in a job)
# ============================================================================

class EmailVerificationItemORM(Base):
    """Individual email verification item within a job"""
    __tablename__ = "email_verification_items"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("email_verification_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Email data
    raw_email = Column(String(255), nullable=False)  # Email text for CSV jobs
    
    # Processing status
    status = Column(String(20), nullable=False, default="pending", index=True)  # 'pending', 'processing', 'done', 'error'
    
    # Verification result
    verify_status = Column(String(20), nullable=True)  # 'valid', 'invalid', 'risky', 'unknown', 'disposable', 'syntax_error'
    verify_reason = Column(Text, nullable=True)
    verify_confidence = Column(Numeric(3, 2), nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    job = relationship("EmailVerificationJobORM", back_populates="items")
    email_record = relationship("EmailORM")
    
    __table_args__ = (
        Index("idx_email_ver_items_job", "job_id"),
        Index("idx_email_ver_items_status", "job_id", "status"),
    )

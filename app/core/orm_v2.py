"""Advanced AI/ML ORM models for LeadFlux AI v2 - Identity Graph, Social Intel, etc."""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Enum as SQLEnum, Text, Numeric, Index, UniqueConstraint, JSON, Float
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType, ArrayType  # Reuse existing type helpers


# ============================================================================
# Identity Graph: Entities & Relationships
# ============================================================================

class EntityType(str, PyEnum):
    """Types of entities in the identity graph"""
    company = "company"
    person = "person"
    domain = "domain"
    linkedin_company = "linkedin_company"
    linkedin_profile = "linkedin_profile"
    twitter_profile = "twitter_profile"
    facebook_page = "facebook_page"
    instagram_profile = "instagram_profile"
    directory_entry = "directory_entry"
    email_address = "email_address"
    phone_number = "phone_number"


class EdgeType(str, PyEnum):
    """Types of relationships between entities"""
    works_at = "works_at"
    owns = "owns"
    mentions = "mentions"
    follows = "follows"
    same_group = "same_group"
    from_directory = "from_directory"
    same_domain = "same_domain"
    social_connection = "social_connection"
    email_belongs_to = "email_belongs_to"
    phone_belongs_to = "phone_belongs_to"


class EntityORM(Base):
    """Entity in the identity graph (company, person, domain, social profile, etc.)"""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Entity identity
    type = Column(SQLEnum(EntityType), nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)  # LinkedIn ID, Twitter handle, etc.
    name = Column(String(500), nullable=True, index=True)
    url = Column(String(1000), nullable=True)
    
    # Flexible data storage
    data = Column(JsonType, nullable=False, default=dict)  # Platform-specific fields
    
    # Decision maker scoring (GNN output)
    decision_maker_score = Column(Float, nullable=True)  # 0-1, for person entities
    decision_maker_role = Column(String(100), nullable=True)  # "Primary", "Secondary", "Influencer"
    
    # Relationships
    organization = relationship("OrganizationORM")
    out_edges = relationship("EdgeORM", foreign_keys="EdgeORM.src_entity_id", back_populates="source")
    in_edges = relationship("EdgeORM", foreign_keys="EdgeORM.dst_entity_id", back_populates="target")
    embeddings = relationship("EntityEmbeddingORM", back_populates="entity")
    
    __table_args__ = (
        Index("idx_entity_org_type", "organization_id", "type"),
        Index("idx_entity_external", "external_id", "type"),
    )


class EdgeORM(Base):
    """Relationship between entities"""
    __tablename__ = "edges"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Edge definition
    src_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    dst_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(EdgeType), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)  # Relationship strength
    
    # Edge metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    edge_metadata = Column(JsonType, nullable=False, default=dict)
    
    # Relationships
    organization = relationship("OrganizationORM")
    source = relationship("EntityORM", foreign_keys=[src_entity_id], back_populates="out_edges")
    target = relationship("EntityORM", foreign_keys=[dst_entity_id], back_populates="in_edges")
    
    __table_args__ = (
        UniqueConstraint("src_entity_id", "dst_entity_id", "type", name="uq_edge"),
        Index("idx_edge_src_type", "src_entity_id", "type"),
        Index("idx_edge_dst_type", "dst_entity_id", "type"),
    )


class EntityEmbeddingORM(Base):
    """Embeddings for entities (for GNN, similarity search, etc.)"""
    __tablename__ = "entity_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Embedding details
    kind = Column(String(50), nullable=False, index=True)  # "text", "social", "combined", "gnn"
    model = Column(String(100), nullable=False)  # "mpnet-base", "sentence-transformers/all-MiniLM-L6-v2"
    dimension = Column(Integer, nullable=False)
    vector = Column(ArrayType(Float), nullable=False)  # Embedding vector
    
    # Relationships
    entity = relationship("EntityORM", back_populates="embeddings")
    
    __table_args__ = (
        UniqueConstraint("entity_id", "kind", name="uq_entity_embedding"),
    )


# ============================================================================
# Social Content Intelligence
# ============================================================================

class SocialPostORM(Base):
    """Social media posts from companies/people"""
    __tablename__ = "social_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link to entity (company or person)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Post identity
    platform = Column(String(50), nullable=False, index=True)  # "linkedin", "twitter", "facebook"
    post_id = Column(String(255), nullable=True, index=True)  # Platform-specific ID
    url = Column(String(1000), nullable=True)
    
    # Content
    text = Column(Text, nullable=True)
    created_at_post = Column(DateTime(timezone=True), nullable=True, index=True)  # When post was created on platform
    
    # Metrics
    metrics = Column(JsonType, nullable=False, default=dict)  # likes, comments, shares, views
    
    # AI analysis
    topics = Column(ArrayType(String), nullable=True)  # Extracted topics
    sentiment = Column(String(20), nullable=True)  # "positive", "neutral", "negative"
    embedding = Column(ArrayType(Float), nullable=True)  # Post embedding for clustering
    
    # Relationships
    organization = relationship("OrganizationORM")
    entity = relationship("EntityORM")
    
    __table_args__ = (
        UniqueConstraint("platform", "post_id", name="uq_social_post"),
        Index("idx_social_entity_platform", "entity_id", "platform"),
        Index("idx_social_created", "created_at_post"),
    )


class SocialInsightORM(Base):
    """Aggregated social insights per entity"""
    __tablename__ = "social_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Aggregated metrics
    posts_per_month = Column(Float, nullable=True)
    avg_engagement = Column(Float, nullable=True)
    total_followers = Column(Integer, nullable=True)
    
    # Topic distribution
    topic_distribution = Column(JsonType, nullable=False, default=dict)  # {"topic": count}
    dominant_topics = Column(ArrayType(String), nullable=True)  # Top 5 topics
    
    # Sentiment
    sentiment_distribution = Column(JsonType, nullable=False, default=dict)  # {"positive": 0.6, "neutral": 0.3, "negative": 0.1}
    
    # AI classifications
    growth_stage = Column(String(50), nullable=True)  # "early", "scaling", "mature"
    dominant_pain = Column(String(100), nullable=True)  # "lead_gen", "ops", "hiring", "software", "reputation"
    
    # Summary text (LLM-generated)
    summary = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    entity = relationship("EntityORM")
    
    __table_args__ = (
        UniqueConstraint("entity_id", name="uq_social_insight_entity"),
    )


# ============================================================================
# RL / Bandit: Next Best Action
# ============================================================================

class ActionType(str, PyEnum):
    """Types of outreach actions"""
    email_template_a = "email_template_a"
    email_template_b = "email_template_b"
    email_template_c = "email_template_c"
    linkedin_dm = "linkedin_dm"
    linkedin_connection = "linkedin_connection"
    call = "call"
    skip = "skip"
    wait = "wait"


class NextActionORM(Base):
    """Recommended next action for a lead"""
    __tablename__ = "next_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link to lead
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Recommendation
    action = Column(SQLEnum(ActionType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0-1, model confidence
    reason = Column(Text, nullable=True)  # Human-readable explanation
    
    # Timing
    suggested_at = Column(DateTime(timezone=True), nullable=True)  # When to execute
    
    # Model info
    model_version = Column(String(50), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    lead = relationship("LeadORM")
    
    __table_args__ = (
        UniqueConstraint("lead_id", name="uq_next_action_lead"),
    )


class ActionOutcomeORM(Base):
    """Outcome of an action (for RL training)"""
    __tablename__ = "action_outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Action taken
    action = Column(SQLEnum(ActionType), nullable=False)
    action_taken_at = Column(DateTime(timezone=True), nullable=False, index=True)
    suggested_by_ai = Column(Boolean, nullable=False, default=False)
    
    # Outcome
    outcome = Column(String(50), nullable=True, index=True)  # "won", "replied", "booked_call", "no_response", "unsubscribed", "complaint"
    outcome_at = Column(DateTime(timezone=True), nullable=True)
    reward = Column(Float, nullable=True)  # Calculated reward for RL
    
    # Action metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    action_metadata = Column(JsonType, nullable=False, default=dict)
    
    # Relationships
    organization = relationship("OrganizationORM")
    lead = relationship("LeadORM")
    
    __table_args__ = (
        Index("idx_action_lead_outcome", "lead_id", "outcome"),
    )


class PersonScoreORM(Base):
    """Decision maker scores for people entities"""
    __tablename__ = "person_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Entity references
    person_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    company_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Scoring
    decision_maker_score = Column(Float, nullable=False)  # 0-1
    role = Column(String(100), nullable=True)  # "Primary", "Secondary", "Influencer"
    reason = Column(Text, nullable=True)  # Human-readable explanation
    
    # Relationships
    organization = relationship("OrganizationORM")
    person_entity = relationship("EntityORM", foreign_keys=[person_entity_id])
    company_entity = relationship("EntityORM", foreign_keys=[company_entity_id])
    lead = relationship("LeadORM")
    
    __table_args__ = (
        UniqueConstraint("person_entity_id", "company_entity_id", name="uq_person_score"),
        Index("idx_person_score_lead", "lead_id", "decision_maker_score"),
    )


# ============================================================================
# AI Workflow DSL
# ============================================================================

class WorkflowORM(Base):
    """AI-generated or user-defined workflow"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Workflow identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # DSL specification (JSON)
    spec = Column(JsonType, nullable=False)  # Workflow DSL JSON
    
    # Generation info
    is_ai_generated = Column(Boolean, nullable=False, default=False)
    natural_language_prompt = Column(Text, nullable=True)  # Original user prompt if AI-generated
    
    # Relationships
    organization = relationship("OrganizationORM")
    # jobs relationship removed - add workflow_id foreign key to ScrapeJobORM first if needed
    
    __table_args__ = (
        Index("idx_workflow_org", "organization_id"),
    )


# ============================================================================
# Multi-Agent Deep Research Dossiers
# ============================================================================

class DossierStatus(str, PyEnum):
    """Dossier generation status"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class DossierORM(Base):
    """Deep AI research dossier for a lead"""
    __tablename__ = "dossiers"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link to lead
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status tracking
    status = Column(SQLEnum(DossierStatus), nullable=False, default=DossierStatus.pending, index=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dossier content (structured JSONB for flexibility)
    sections = Column(JsonType, nullable=True)  # {"overview": "...", "offer": "...", etc.}
    
    # Legacy fields (kept for backward compatibility, can be populated from sections)
    business_summary = Column(Text, nullable=True)
    offerings = Column(ArrayType(String), nullable=True)
    target_audience = Column(Text, nullable=True)
    digital_maturity = Column(Text, nullable=True)
    tech_stack_summary = Column(Text, nullable=True)
    recent_initiatives = Column(ArrayType(String), nullable=True)
    risks_constraints = Column(Text, nullable=True)
    suggested_outreach_angle = Column(Text, nullable=True)
    sample_email = Column(Text, nullable=True)
    sample_linkedin_message = Column(Text, nullable=True)
    
    # Agent execution info
    agents_used = Column(ArrayType(String), nullable=True)  # ["web", "social", "tech", "analyst"]
    execution_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    lead = relationship("LeadORM")
    
    __table_args__ = (
        UniqueConstraint("lead_id", name="uq_dossier_lead"),
    )


# ============================================================================
# Cross-Org Trend & Anomaly Detection
# ============================================================================

class TrendORM(Base):
    """Market trends detected across organizations"""
    __tablename__ = "trends"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Trend identity
    niche = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True, index=True)
    period = Column(String(50), nullable=False, index=True)  # "2024-01", "2024-Q1"
    
    # Metrics
    avg_smart_score = Column(Float, nullable=True)
    email_coverage = Column(Float, nullable=True)
    phone_coverage = Column(Float, nullable=True)
    lead_count = Column(Integer, nullable=False)
    avg_digital_maturity = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)  # If outcomes available
    
    # Change detection
    change_from_previous = Column(Float, nullable=True)  # Percentage change
    is_hot_opportunity = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    __table_args__ = (
        UniqueConstraint("niche", "location", "period", name="uq_trend"),
        Index("idx_trend_hot", "is_hot_opportunity", "change_from_previous"),
    )


class AnomalyORM(Base):
    """Detected anomalies in scraping/jobs"""
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Anomaly identity
    anomaly_type = Column(String(100), nullable=False, index=True)  # "scraping_success_drop", "api_error_spike", etc.
    severity = Column(String(20), nullable=False, index=True)  # "low", "medium", "high", "critical"
    
    # Context
    niche = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True, index=True)
    source = Column(String(100), nullable=True, index=True)
    
    # Detection details
    detected_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    deviation_pct = Column(Float, nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    suggested_action = Column(Text, nullable=True)
    
    # Status
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_anomaly_severity", "severity", "is_resolved"),
    )


# ============================================================================
# Social Connectors (OAuth tokens, etc.)
# ============================================================================

class SocialConnectorORM(Base):
    """OAuth connections to social platforms"""
    __tablename__ = "social_connectors"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Platform
    platform = Column(String(50), nullable=False, index=True)  # "linkedin", "twitter", "facebook"
    
    # OAuth tokens (encrypted)
    access_token = Column(Text, nullable=True)  # Should be encrypted in production
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Connection status
    is_active = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Platform-specific data
    platform_user_id = Column(String(255), nullable=True)
    platform_username = Column(String(255), nullable=True)
    connector_metadata = Column(JsonType, nullable=False, default=dict)
    
    # Relationships
    organization = relationship("OrganizationORM")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "platform", name="uq_social_connector"),
    )


"""Universal Robots ORM models"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, func, ForeignKey, 
    Enum as SQLEnum, Text, Numeric, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.db import Base
from app.core.orm import JsonType, ArrayType


class RobotMode(str, PyEnum):
    """Robot creation mode"""
    ai = "ai"
    manual = "manual"


class RobotRunStatus(str, PyEnum):
    """Robot run status"""
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class URLStatus(str, PyEnum):
    """URL processing status"""
    pending = "pending"
    done = "done"
    error = "error"


class RobotORM(Base):
    """Universal robot definition"""
    __tablename__ = "robots"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Robot identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    mode = Column(SQLEnum(RobotMode), nullable=False, default=RobotMode.ai)
    
    # AI generation inputs
    prompt = Column(Text, nullable=True)  # Original user description
    sample_url = Column(String(1000), nullable=True)  # Sample URL for testing
    
    # Robot configuration
    schema = Column(JsonType, nullable=False)  # [{name, type, required}, ...]
    workflow_spec = Column(JsonType, nullable=False)  # DSL for execution
    
    # Relationships
    organization = relationship("OrganizationORM")
    runs = relationship("RobotRunORM", back_populates="robot", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_robot_org", "organization_id"),
    )


class RobotRunORM(Base):
    """Robot execution run"""
    __tablename__ = "robot_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Robot reference
    robot_id = Column(Integer, ForeignKey("robots.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Run status
    status = Column(SQLEnum(RobotRunStatus), nullable=False, default=RobotRunStatus.queued, index=True)
    
    # Progress tracking
    total_urls = Column(Integer, nullable=True)
    processed_urls = Column(Integer, nullable=False, default=0)
    total_rows = Column(Integer, nullable=False, default=0)
    
    # Error handling
    error = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("OrganizationORM")
    robot = relationship("RobotORM", back_populates="runs")
    urls = relationship("RobotRunUrlORM", back_populates="run", cascade="all, delete-orphan")
    rows = relationship("RobotRunRowORM", back_populates="run", cascade="all, delete-orphan")
    imported_leads = relationship("LeadORM", back_populates="source_robot_run")
    
    __table_args__ = (
        Index("idx_robot_run_robot_status", "robot_id", "status"),
        Index("idx_robot_run_org", "organization_id"),
    )


class RobotRunUrlORM(Base):
    """URLs to process in a robot run"""
    __tablename__ = "robot_run_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    run_id = Column(Integer, ForeignKey("robot_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    url = Column(String(2000), nullable=False)
    status = Column(SQLEnum(URLStatus), nullable=False, default=URLStatus.pending, index=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    run = relationship("RobotRunORM", back_populates="urls")
    
    __table_args__ = (
        Index("idx_robot_url_run_status", "run_id", "status"),
    )


class RobotRunRowORM(Base):
    """Extracted data rows from a robot run"""
    __tablename__ = "robot_run_rows"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    run_id = Column(Integer, ForeignKey("robot_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_url = Column(String(2000), nullable=False)
    data = Column(JsonType, nullable=False)  # Extracted fields as JSON
    
    # Relationships
    run = relationship("RobotRunORM", back_populates="rows")
    
    __table_args__ = (
        Index("idx_robot_row_run", "run_id"),
    )


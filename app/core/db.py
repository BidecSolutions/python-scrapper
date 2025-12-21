"""Database configuration and session management (SYNC version)"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from app.core.config import settings


# Convert async URL to sync URL if needed
DATABASE_URL = settings.DATABASE_URL
# Replace async drivers with sync ones
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
elif DATABASE_URL.startswith("sqlite+aiosqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")

# SQLite-specific configuration
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Dependency for getting database session (sync)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional async session support for background AI tasks.
try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    ASYNC_DATABASE_URL = settings.DATABASE_URL
    if ASYNC_DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    elif ASYNC_DATABASE_URL.startswith("sqlite://"):
        ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
except Exception:
    AsyncSessionLocal = None


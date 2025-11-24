"""Migration script to create v2 AI/ML tables"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.db import Base

# Import all ORM models to register them
from app.core.orm import *  # noqa
from app.core.orm_v2 import *  # noqa

def migrate():
    """Create v2 tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating v2 AI/ML tables...")
    
    # Create tables
    Base.metadata.create_all(engine)
    
    print("SUCCESS: Migration complete!")
    print("\nCreated tables:")
    print("  - entities (identity graph)")
    print("  - edges (relationships)")
    print("  - entity_embeddings")
    print("  - social_posts")
    print("  - social_insights")
    print("  - next_actions")
    print("  - action_outcomes")
    print("  - workflows")
    print("  - dossiers")
    print("  - trends")
    print("  - anomalies")
    print("  - social_connectors")

if __name__ == "__main__":
    migrate()


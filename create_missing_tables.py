"""Create all missing database tables using SQLAlchemy Base.metadata.create_all()"""
import sys
from app.core.db import Base, engine

# Import all ORM modules to register tables with Base.metadata
print("Importing ORM modules...")
from app.core import orm  # Main ORM models
from app.core import orm_agency  # Agency models
from app.core import orm_workspaces  # Workspace models
from app.core import orm_api_keys  # API key models
from app.core import orm_companies  # Company models
from app.core import orm_tech_intent  # Tech & intent models
from app.core import orm_ai_playbook  # AI playbook models
from app.core import orm_campaigns  # Campaign models
from app.core import orm_email_sync  # Email sync models
from app.core import orm_tasks_notes  # Tasks & notes models
from app.core import orm_activity  # Activity models
from app.core import orm_notifications  # Notification models
from app.core import orm_deals  # Deal models
from app.core import orm_health  # Health metrics models
from app.core import orm_templates  # Template models
from app.core import orm_lookalike  # Lookalike models
from app.core import orm_integrations  # Integration models
from app.core import orm_segments  # Segment models
from app.core import orm_lists  # List models
from app.core import orm_company_search  # Company search models
from app.core import orm_playbooks  # Playbook models
from app.core import orm_v2  # V2 AI models
from app.core import orm_robots  # Robot models
from app.core import orm_saved_views  # Saved views models
from app.core import orm_duplicates  # Duplicate detection models

print("Creating all missing tables...")
try:
    # This will create all tables in the correct order based on foreign key dependencies
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("SUCCESS: All tables created successfully!")
    print("\nNote: If a table already exists, it was skipped (checkfirst=True).")
except Exception as e:
    print(f"\nERROR: Failed to create tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Database Migration: Add Logo URL to Organizations

## Overview
This migration adds a `logo_url` field to the `organizations` table to support custom organization logos.

## Manual Migration (SQLite/PostgreSQL)

### For SQLite:
```sql
ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512);
```

### For PostgreSQL:
```sql
ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512);
```

## Python Migration Script

If you're using Alembic or want to run a Python migration:

```python
from app.core.db import engine, Base
from sqlalchemy import text

# Run migration
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE organizations ADD COLUMN logo_url VARCHAR(512)"))
    conn.commit()
```

## Verification

After running the migration, verify the column exists:

```sql
-- SQLite
PRAGMA table_info(organizations);

-- PostgreSQL
\d organizations
```

You should see `logo_url` in the column list.

## Notes

- The `logo_url` column is nullable (allows NULL)
- Existing organizations will have `logo_url = NULL` (will use default logo)
- Logo files are stored in `uploads/logos/` directory
- Logo URLs are served via `/uploads/logos/` endpoint


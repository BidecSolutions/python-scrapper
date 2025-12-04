"""Check if duplicate tables exist"""
from app.core.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check duplicate_groups
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name IN ('duplicate_groups', 'duplicate_leads')
        ORDER BY table_name
    """))
    tables = result.fetchall()
    
    if tables:
        print("✅ Duplicate tables found:")
        for table in tables:
            table_name = table[0]
            print(f"\n  - {table_name}")
            
            # Check columns
            result = conn.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print(f"    Columns ({len(columns)}):")
            for col_name, col_type in columns[:10]:  # Show first 10
                print(f"      - {col_name}: {col_type}")
            if len(columns) > 10:
                print(f"      ... and {len(columns) - 10} more")
    else:
        print("❌ Duplicate tables do NOT exist!")


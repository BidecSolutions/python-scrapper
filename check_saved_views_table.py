"""Check if saved_views table exists"""
from app.core.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'saved_views'
    """))
    table = result.fetchone()
    
    if table:
        print("✅ saved_views table exists!")
        
        # Check columns
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'saved_views'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print(f"\nTable has {len(columns)} columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
    else:
        print("❌ saved_views table does NOT exist!")


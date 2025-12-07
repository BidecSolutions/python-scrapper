"""Check if leads are saved for a specific job"""
import sys
import os
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

def check_job_leads(job_id: int = None):
    print("=" * 70)
    print("Checking Job Leads")
    print("=" * 70)
    
    db_url = settings.DATABASE_URL
    
    # Convert async URL to sync if needed
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # List all jobs
        result = conn.execute(text("""
            SELECT id, niche, location, status, result_count, created_at, error_message
            FROM scrape_jobs
            ORDER BY id DESC
            LIMIT 10
        """))
        jobs = result.fetchall()
        
        print(f"\n📋 Recent Jobs (last 10):")
        for job in jobs:
            jid, niche, location, status, result_count, created_at, error_msg = job
            print(f"\n  Job ID: {jid}")
            print(f"    Niche: {niche}")
            print(f"    Location: {location or 'N/A'}")
            print(f"    Status: {status}")
            print(f"    Result Count: {result_count}")
            print(f"    Created: {created_at}")
            if error_msg:
                print(f"    ⚠️  Error: {error_msg[:100]}")
            
            # Check leads for this job
            lead_result = conn.execute(
                text("SELECT COUNT(*) FROM leads WHERE job_id = :job_id"),
                {"job_id": jid}
            )
            lead_count = lead_result.scalar()
            print(f"    ✅ Leads in database: {lead_count}")
            
            if lead_count > 0:
                # Show sample leads
                sample_result = conn.execute(
                    text("SELECT id, name, website, source FROM leads WHERE job_id = :job_id LIMIT 5"),
                    {"job_id": jid}
                )
                samples = sample_result.fetchall()
                print(f"    Sample leads:")
                for sample in samples:
                    sid, name, website, source = sample
                    print(f"      - {name} ({website or 'no website'}) [{source}]")
        
        # If specific job_id provided, show detailed info
        if job_id:
            print(f"\n" + "=" * 70)
            print(f"Detailed Info for Job {job_id}")
            print("=" * 70)
            
            result = conn.execute(
                text("SELECT * FROM scrape_jobs WHERE id = :job_id"),
                {"job_id": job_id}
            )
            job = result.fetchone()
            
            if job:
                print(f"\nJob Details:")
                print(f"  Niche: {job[5] if len(job) > 5 else 'N/A'}")
                print(f"  Status: {job[11] if len(job) > 11 else 'N/A'}")
                print(f"  Result Count: {job[12] if len(job) > 12 else 'N/A'}")
                
                # Count leads
                lead_result = conn.execute(
                    text("SELECT COUNT(*) FROM leads WHERE job_id = :job_id"),
                    {"job_id": job_id}
                )
                lead_count = lead_result.scalar()
                print(f"\n  Leads in database: {lead_count}")
                
                if lead_count > 0:
                    # Show all leads
                    leads_result = conn.execute(
                        text("SELECT id, name, website, emails, phones, source FROM leads WHERE job_id = :job_id"),
                        {"job_id": job_id}
                    )
                    leads = leads_result.fetchall()
                    print(f"\n  All Leads:")
                    for lead in leads:
                        lid, name, website, emails, phones, source = lead
                        email_str = emails[0] if emails and len(emails) > 0 else "No email"
                        phone_str = phones[0] if phones and len(phones) > 0 else "No phone"
                        print(f"    - {name}")
                        print(f"      Website: {website or 'N/A'}")
                        print(f"      Email: {email_str}")
                        print(f"      Phone: {phone_str}")
                        print(f"      Source: {source}")
            else:
                print(f"\n❌ Job {job_id} not found!")

if __name__ == "__main__":
    import sys
    job_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    check_job_leads(job_id)


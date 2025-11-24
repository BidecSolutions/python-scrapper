# Email Finder & Verifier - Complete Design

## Overview

Integrate Email Finder and Verifier as first-class features in LeadFlux, with proper job management, credit tracking, and bulk processing capabilities.

## Current State

✅ **Already Implemented:**
- Basic email verification logic (`app/services/email_verifier.py`)
- Basic email finding logic (`app/services/email_finder.py`)
- API endpoints (`app/api/routes_email.py`)
- UI page (`frontend/app/email-finder/page.tsx`)
- Database model for caching (`EmailVerificationORM`)

❌ **Missing:**
- Job-based bulk processing
- Credit tracking per operation
- Integration with existing Lead model
- Bulk finder jobs
- Historical tracking and analytics
- Rate limiting per organization

---

## Database Schema

### New Tables

```sql
-- Email Finder Jobs (similar to scraping jobs)
CREATE TABLE email_finder_jobs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Job metadata
    name VARCHAR(255),  -- Optional: "Find emails for Q1 campaign"
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed
    error_message TEXT,
    
    -- Input: CSV data or manual entries
    input_data JSONB,  -- Array of {first_name, last_name, company, domain}
    total_inputs INTEGER DEFAULT 0,
    
    -- Progress tracking
    processed_count INTEGER DEFAULT 0,
    found_count INTEGER DEFAULT 0,
    not_found_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    
    -- Settings
    skip_smtp BOOLEAN DEFAULT FALSE,
    min_confidence DECIMAL(3,2) DEFAULT 0.3,
    auto_save_to_leads BOOLEAN DEFAULT FALSE,
    target_list_id INTEGER REFERENCES lead_lists(id),  -- Optional: save to specific list
    
    -- Results
    results JSONB,  -- Array of find results
    
    -- Credits
    credits_used INTEGER DEFAULT 0,
    
    INDEX idx_email_finder_jobs_org (organization_id),
    INDEX idx_email_finder_jobs_status (status),
    INDEX idx_email_finder_jobs_created (created_at)
);

-- Email Verification Jobs (bulk verification)
CREATE TABLE email_verification_jobs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Job metadata
    name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    
    -- Input: List of emails
    input_emails TEXT[],  -- Array of email addresses
    total_emails INTEGER DEFAULT 0,
    
    -- Progress tracking
    processed_count INTEGER DEFAULT 0,
    valid_count INTEGER DEFAULT 0,
    invalid_count INTEGER DEFAULT 0,
    risky_count INTEGER DEFAULT 0,
    unknown_count INTEGER DEFAULT 0,
    disposable_count INTEGER DEFAULT 0,
    gibberish_count INTEGER DEFAULT 0,
    
    -- Settings
    skip_smtp BOOLEAN DEFAULT FALSE,
    
    -- Results
    results JSONB,  -- Array of verification results
    
    -- Credits
    credits_used INTEGER DEFAULT 0,
    
    INDEX idx_email_verification_jobs_org (organization_id),
    INDEX idx_email_verification_jobs_status (status)
);

-- Email Finder Results (individual records)
CREATE TABLE email_finder_results (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES email_finder_jobs(id) ON DELETE CASCADE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Input
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    company VARCHAR(255),
    domain VARCHAR(255),
    
    -- Output
    found_email VARCHAR(255),
    status VARCHAR(50),  -- found, not_found, error
    confidence DECIMAL(3,2),
    verification_status VARCHAR(50),  -- valid, invalid, risky, unknown
    verification_reason VARCHAR(100),
    
    -- Metadata
    candidates_checked INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Link to lead (if auto-saved)
    lead_id INTEGER REFERENCES leads(id),
    
    INDEX idx_email_finder_results_org (organization_id),
    INDEX idx_email_finder_results_job (job_id),
    INDEX idx_email_finder_results_domain (domain)
);
```

### Updates to Existing Tables

```sql
-- Add credits tracking to organizations
ALTER TABLE organizations ADD COLUMN credits_balance INTEGER DEFAULT 0;
ALTER TABLE organizations ADD COLUMN credits_limit INTEGER DEFAULT 1000;  -- Per month
ALTER TABLE organizations ADD COLUMN credits_reset_at TIMESTAMP WITH TIME ZONE;

-- Add usage tracking
CREATE TABLE credit_transactions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL,  -- 'deduction', 'grant', 'reset'
    amount INTEGER NOT NULL,  -- Positive for grants, negative for deductions
    balance_after INTEGER NOT NULL,
    
    -- Context
    feature VARCHAR(50),  -- 'email_finder', 'email_verifier', 'scraping_job', 'robot_run'
    reference_id INTEGER,  -- Job ID, etc.
    reference_type VARCHAR(50),  -- 'email_finder_job', 'verification_job', etc.
    
    description TEXT,
    
    INDEX idx_credit_transactions_org (organization_id),
    INDEX idx_credit_transactions_created (created_at)
);
```

---

## API Endpoints

### Email Finder

```python
# Single find (existing, but add credit tracking)
POST /api/email-finder
  - Deduct 1 credit
  - Return result

# Bulk find job (NEW)
POST /api/email-finder/jobs
  Request: {
    name?: string,
    inputs: Array<{first_name, last_name, company?, domain?}>,
    skip_smtp?: boolean,
    min_confidence?: number,
    auto_save_to_leads?: boolean,
    target_list_id?: number
  }
  Response: { job_id, status, total_inputs, estimated_credits }

GET /api/email-finder/jobs
  - List all finder jobs for org
  - Filter by status, date range

GET /api/email-finder/jobs/{job_id}
  - Get job details + results

GET /api/email-finder/jobs/{job_id}/results
  - Paginated results
  - Filter by status, confidence

POST /api/email-finder/jobs/{job_id}/export
  - Export results as CSV/Excel

POST /api/email-finder/jobs/{job_id}/save-to-leads
  - Bulk save found emails to leads
```

### Email Verifier

```python
# Single verify (existing, but add credit tracking)
POST /api/email-verifier
  - Deduct 0.5 credits
  - Return result

# Bulk verify job (NEW)
POST /api/email-verifier/jobs
  Request: {
    name?: string,
    emails: string[],
    skip_smtp?: boolean
  }
  Response: { job_id, status, total_emails, estimated_credits }

GET /api/email-verifier/jobs
  - List all verification jobs

GET /api/email-verifier/jobs/{job_id}
  - Get job details + results

GET /api/email-verifier/jobs/{job_id}/results
  - Paginated results
  - Filter by status

POST /api/email-verifier/jobs/{job_id}/export
  - Export results as CSV/Excel
```

### Credits & Usage

```python
GET /api/credits/balance
  - Current balance, limit, reset date

GET /api/credits/usage
  - Usage breakdown by feature
  - Time range filter

GET /api/credits/transactions
  - Paginated transaction history
```

---

## Background Job Processing

### Email Finder Job Processor

```python
# app/services/email_finder_job_processor.py

async def process_finder_job(job_id: int):
    """
    Process an email finder job in the background
    
    1. Load job from DB
    2. For each input:
       - Resolve domain if needed
       - Call find_email()
       - Save result to email_finder_results
       - Update job progress
       - Deduct credit
    3. Mark job as completed
    4. If auto_save_to_leads: bulk create leads
    """
```

### Email Verifier Job Processor

```python
# app/services/email_verifier_job_processor.py

async def process_verification_job(job_id: int):
    """
    Process an email verification job in the background
    
    1. Load job from DB
    2. For each email:
       - Check cache first (EmailVerificationORM)
       - If not cached: call verify_email()
       - Save to cache + email_verification_jobs.results
       - Update job progress
       - Deduct credit (0.5 per verify)
    3. Mark job as completed
    """
```

---

## Frontend UI

### Email Finder Page Updates

1. **Single Finder Tab** (existing, keep)
2. **Bulk Finder Tab** (NEW)
   - Upload CSV or paste data
   - Preview inputs
   - Start job
   - View job progress
   - Download results

3. **Finder Jobs Tab** (NEW)
   - List all jobs
   - Status badges
   - Quick stats (found/not found)
   - Actions: View, Export, Delete

### Email Verifier Page Updates

1. **Single Verifier Tab** (existing, keep)
2. **Bulk Verifier Tab** (existing, enhance)
   - Show as job-based
   - Progress tracking
   - Export results

3. **Verification Jobs Tab** (NEW)
   - List all jobs
   - Status breakdown
   - Export results

### Credits Dashboard (NEW)

- Current balance
- Usage chart (by feature)
- Transaction history
- Upgrade prompt if low

---

## Credit System

### Credit Costs

- **Email Finder**: 1 credit per find
- **Email Verifier**: 0.5 credits per verify
- **Scraping Job**: 10 credits per job (or per 100 leads)
- **Robot Run**: 5 credits per run

### Credit Management

```python
# app/services/credit_manager.py

class CreditManager:
    def check_balance(org_id, required_credits) -> bool
    def deduct_credits(org_id, amount, feature, reference_id) -> bool
    def grant_credits(org_id, amount, reason) -> None
    def reset_monthly_credits(org_id) -> None
    def get_usage_stats(org_id, start_date, end_date) -> dict
```

---

## Integration Points

### With Existing Leads

- **Auto-save option**: When finding emails, automatically create/update leads
- **Lead enrichment**: Add "email_finder" as a source
- **Quality scoring**: Use verification status in lead quality calculation

### With Jobs

- **Link finder jobs to scraping jobs**: "Find emails for leads from Job #123"
- **Unified job list**: Show both scraping and finder jobs together

### With Lists/Campaigns

- **Save to list**: Option to save found emails directly to a named list
- **List enrichment**: "Find emails for all leads in List X"

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Database migrations (new tables)
2. Credit manager service
3. Background job processors
4. API endpoints for jobs

### Phase 2: UI
1. Bulk finder UI
2. Jobs list pages
3. Credits dashboard
4. Export functionality

### Phase 3: Integration
1. Auto-save to leads
2. Link to scraping jobs
3. List management
4. Analytics

### Phase 4: Advanced
1. Rate limiting
2. Webhooks
3. CRM integrations
4. API key management

---

## Example Flow

### User Flow: Bulk Email Finder

1. User goes to Email Finder → Bulk Finder tab
2. Uploads CSV with 100 rows (name, company)
3. Clicks "Start Job"
   - Backend creates `email_finder_job`
   - Checks credits (needs 100 credits)
   - Starts background task
4. User sees job in "Jobs" tab with progress
5. Background processor:
   - For each row: find email, deduct credit, save result
6. Job completes: 85 found, 15 not found
7. User exports results as CSV
8. Optionally saves all found emails to leads

---

## Next Steps

1. Create database migrations
2. Implement credit manager
3. Create job processors
4. Add API endpoints
5. Build UI components
6. Add integration hooks


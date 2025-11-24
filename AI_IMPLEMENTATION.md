# AI/ML Implementation Guide

This document describes the AI-powered features integrated into the Lead Scraper platform.

## 🎯 Overview

The platform now includes AI/ML capabilities for:
- **LLM-based structured extraction** (better than regex for messy HTML)
- **Lead quality scoring** (rule-based, ready for ML models)
- **Automatic tagging** (services, features, quality labels)
- **Language detection** (future)
- **Clustering** (future - for market segmentation)

---

## 🏗️ Architecture

### High-Level Flow

```
User → API → Job Queue → Scraper Worker → AI Worker → Database
```

1. **API** creates a scraping job
2. **Scraper Worker**:
   - Finds leads from sources (Google Places, web search)
   - Crawls websites
   - Extracts contacts (regex)
   - Saves raw text snapshots
   - Enqueues AI enrichment tasks
3. **AI Worker**:
   - Loads website text from snapshots
   - Calls LLM for structured extraction
   - Calculates quality score
   - Extracts tags
   - Updates lead in database

---

## 📊 Database Schema

### New AI Fields in `leads` Table

- `language` (TEXT) - Detected language ("en", "ur", "ar")
- `tags` (JSONB) - General-purpose tags (["24_7", "online_booking", "premium"])
- `quality_score` (NUMERIC) - 0-100 quality score
- `quality_label` (TEXT) - "low", "medium", "high"
- `cluster_id` (INTEGER) - For market segmentation
- `ai_status` (TEXT) - "pending", "success", "failed"
- `ai_last_error` (TEXT) - Error message if AI processing failed
- `ai_processed_at` (TIMESTAMP) - When AI enrichment completed

### New Tables

#### `lead_snapshots`
Stores raw text from website pages for AI processing:
- `lead_id` - Links to lead
- `page_type` - "home", "contact", "about"
- `url` - Page URL
- `text` - Cleaned text content
- `html_hash` - SHA256 hash for deduplication

#### `lead_embeddings`
Stores embeddings for clustering and semantic search (future):
- `lead_id` - Links to lead
- `model` - Embedding model used
- `dim` - Dimension of vector
- `vector` - Embedding vector (ARRAY)

---

## 🤖 AI Services

### 1. LLM Extractor (`app/ai/llm_extractor.py`)

Extracts structured information from website text using LLM.

**Features**:
- Robust JSON parsing (handles extra text, trailing commas)
- Merge with existing lead data (no overwrite)
- Fallback to regex if LLM fails

**Usage**:
```python
from app.ai.llm_extractor import LLMExtractor

llm_extractor = LLMExtractor(llm_client=your_llm_client)
extracted_data = await llm_extractor.extract(website_text)

# Merge into lead
lead = llm_extractor.merge_with_lead(lead, extracted_data)
```

**Prompt Template**:
- System prompt: Instructions for accurate extraction
- User prompt: Website text + JSON schema
- Response: Structured JSON with fields (emails, phones, services, etc.)

### 2. Lead Scorer (`app/ai/scoring.py`)

Calculates quality score (0-100) using rule-based heuristics.

**Scoring Factors**:
- Email presence & quality (+30)
- Phone presence (+25)
- Website quality (+20)
- Social links (+10)
- Contact person info (+10)
- Tech stack indicators (+5)
- Services/tags (+5)
- Penalties for generic emails, missing website

**ML-Ready Architecture**:
- `LeadScorer`: Rule-based (current)
- `MLLeadScorer`: ML-based (placeholder for future)
- Same interface, easy to swap

**Usage**:
```python
from app.ai.scoring import LeadScorer

scorer = LeadScorer()
score, label = scorer.score_and_label(lead)
# score: 0-100, label: "low", "medium", "high"
```

### 3. AI Enrichment Service (`app/services/ai_enrichment_service.py`)

Orchestrates all AI enrichment:
- LLM extraction
- Quality scoring
- Tag extraction
- Status tracking

**Usage**:
```python
from app.services.ai_enrichment_service import AIEnrichmentService

ai_service = AIEnrichmentService(
    llm_extractor=llm_extractor,
    scorer=scorer
)

success = await ai_service.enrich_lead(db, lead_orm)
```

---

## 🔄 Worker Tasks

### Scraper Worker (`app/workers/scraper_tasks.py`)

Processes scraping jobs:
1. Loads job from database
2. Finds leads from sources
3. Crawls websites
4. Saves leads and snapshots
5. Enqueues AI enrichment tasks

**Usage** (with Celery):
```python
from app.workers.scraper_tasks import scrape_job_celery

scrape_job_celery.delay(job_id, enable_ai=True)
```

### AI Worker (`app/workers/ai_tasks.py`)

Processes AI enrichment:
1. Loads lead and snapshots
2. Calls AI enrichment service
3. Updates lead in database
4. Checks if job is complete

**Usage** (with Celery):
```python
from app.workers.ai_tasks import ai_enrich_lead_celery

ai_enrich_lead_celery.delay(lead_id)
```

---

## 🔌 LLM Client Integration

### Current Implementation

Uses a mock client for testing. To use a real LLM:

### OpenAI Example

```python
import openai
from openai import AsyncOpenAI

class OpenAILLMClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def chat_completion(self, messages, **kwargs):
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # or gpt-4
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
            **kwargs
        )
        return response.choices[0].message.content

# Usage
llm_client = OpenAILLMClient(api_key="your-api-key")
llm_extractor = LLMExtractor(llm_client=llm_client)
```

### Anthropic Example

```python
import anthropic

class AnthropicLLMClient:
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat_completion(self, messages, **kwargs):
        response = await self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            messages=messages,
            **kwargs
        )
        return response.content[0].text

# Usage
llm_client = AnthropicLLMClient(api_key="your-api-key")
llm_extractor = LLMExtractor(llm_client=llm_client)
```

---

## 🚀 Queue Integration

### Option 1: Celery (Recommended)

```bash
pip install celery redis
```

```python
# celery_app.py
from celery import Celery

celery_app = Celery(
    "lead_scraper",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Start workers
# celery -A celery_app worker --loglevel=info
```

### Option 2: RQ (Simpler)

```bash
pip install rq
```

```python
from rq import Queue
from redis import Redis

redis_conn = Redis()
q = Queue(connection=redis_conn)

# Enqueue tasks
q.enqueue(scrape_job_task, job_id)
q.enqueue(ai_enrich_lead_task, lead_id)
```

---

## 📝 Usage Examples

### Complete Job Flow

```python
# 1. Create job via API
job = await create_job(
    niche="dentist clinic",
    location="Karachi",
    max_results=20
)

# 2. Enqueue scraper task (handled by API)
await scrape_job_task(job.id, enable_ai=True)

# Scraper worker will:
# - Find leads
# - Crawl websites
# - Save snapshots
# - Enqueue AI tasks

# AI worker will:
# - Extract with LLM
# - Calculate score
# - Extract tags
# - Update leads

# 3. Check job status
job = await get_job(job.id)
print(f"Status: {job.status}, Leads: {job.result_count}")

# 4. Get enriched leads
leads = await get_leads(job_id=job.id, quality_label="high")
for lead in leads:
    print(f"{lead.name}: {lead.quality_score}, Tags: {lead.tags}")
```

---

## 🎨 LLM Prompt Design

The LLM extractor uses a carefully designed prompt:

**System Prompt**:
- Establishes role as extraction engine
- Emphasizes accuracy over completeness
- Requires valid JSON only

**User Prompt**:
- Provides JSON schema
- Includes guidelines for extraction
- Contains website text (truncated if needed)

**Parsing Strategy**:
1. Direct JSON parse
2. Extract JSON between first `{` and last `}`
3. Regex extraction (last resort)
4. Fallback to regex-based extraction

---

## 📊 Quality Scoring

### Current (Rule-Based)

Simple, transparent scoring:
- Easy to understand and debug
- Fast (no model inference)
- Good starting point

### Future (ML-Based)

When you have enough user feedback:
1. Collect feedback (good/bad/irrelevant)
2. Extract features from leads
3. Train XGBoost/sklearn model
4. Swap `LeadScorer` with `MLLeadScorer`
5. Same interface, better predictions

---

## 🔍 Tags & Filtering

Tags are extracted from:
- Metadata.services → normalized tags
- Service_tags → normalized tags
- Quality_label → "quality_high", etc.
- Feature flags → "has_email", "has_phone", etc.
- CMS → "cms_wordpress", etc.

**Filtering in SQL**:
```sql
-- Leads with specific tags
SELECT * FROM leads
WHERE tags ? 'online_booking'  -- JSONB contains
  AND tags ? '24_7';

-- High-quality leads
SELECT * FROM leads
WHERE quality_label = 'high'
  AND quality_score >= 80;
```

---

## 🎯 Next Steps

1. **Set up LLM client** (OpenAI, Anthropic, etc.)
2. **Set up task queue** (Celery, RQ)
3. **Run migrations** (create new tables/columns)
4. **Test AI extraction** on sample websites
5. **Tune prompts** for your specific use case
6. **Collect feedback** for ML model training
7. **Implement clustering** for market segmentation

---

## 📚 Files Created

- `app/ai/llm_extractor.py` - LLM-based extraction
- `app/ai/scoring.py` - Quality scoring (rule-based + ML-ready)
- `app/services/ai_enrichment_service.py` - AI orchestration
- `app/workers/scraper_tasks.py` - Scraper worker
- `app/workers/ai_tasks.py` - AI worker
- `app/services/text_loader.py` - Load text from snapshots
- `app/core/orm.py` - Updated with AI fields and tables

---

## ⚠️ Notes

- LLM extraction is **optional** - falls back to regex if disabled
- Scoring is **rule-based** by default - easy to upgrade to ML
- Queue integration is **conceptual** - adapt to your task queue choice
- Snapshots are **stored in DB** - consider S3/minio for scale

---

*Ready to transform from scraper to AI-powered lead intelligence platform!* 🚀


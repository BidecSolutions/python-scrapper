# Groq API Key Setup

Your Groq API key has been configured! 🎉

## ✅ Configuration Complete

Your Groq API key has been added to `.env` file. The application will now use it for AI-powered lead enrichment.

## 🚀 Usage

The AI enrichment is **automatic** when you run scraping jobs:

### Option 1: Via API (with job queue)

```python
from app.workers.scraper_tasks import scrape_job_task

# This will automatically use Groq for AI enrichment
await scrape_job_task(job_id=123, enable_ai=True)
```

### Option 2: Direct AI Enrichment

```python
from app.ai.factory import create_llm_client
from app.ai.llm_extractor import LLMExtractor
from app.services.ai_enrichment_service import AIEnrichmentService

# Create Groq client (auto-detected from .env)
llm_client = create_llm_client()  # Uses GROQ_API_KEY from .env

# Use it for extraction
llm_extractor = LLMExtractor(llm_client=llm_client)
```

## 📋 What Groq is Used For

1. **Structured Extraction**: Extract emails, phones, addresses, services from website text
2. **Quality Scoring**: Calculate lead quality scores (0-100)
3. **Automatic Tagging**: Extract service tags and features
4. **Personalization**: Generate outreach notes for each lead

## 🔧 Configuration Options

### Change Model

Edit `.env` or use code:

```python
from app.ai.llm_clients import GroqLLMClient

client = GroqLLMClient(
    api_key="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",
    model="llama-3.1-70b-versatile"  # or "llama-3.1-8b-instant" for faster
)
```

### Available Models

- `llama-3.1-70b-versatile` (default) - Best quality
- `llama-3.1-8b-instant` - Faster, lower cost
- `mixtral-8x7b-32768` - Good balance

## 📦 Install Groq Library

If you haven't already:

```bash
pip install groq
```

## ✅ Verify Setup

Run this to verify your Groq API key is working:

```python
from app.ai.factory import create_llm_client

client = create_llm_client()
if client:
    print("✅ Groq client configured successfully!")
else:
    print("❌ Groq client not available. Check your .env file.")
```

## 🔒 Security Note

- The API key is stored in `.env` (not committed to git)
- Never share or commit your API key
- `.env` is in `.gitignore` for safety

## 🎯 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run a scraping job**: The AI enrichment will happen automatically
3. **Check results**: Leads will have `quality_score`, `tags`, and enriched data

---

**Your Groq API key is ready to use!** 🚀


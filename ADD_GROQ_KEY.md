# Add Groq API Key to .env

## Your Groq API Key
```
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
```

## Instructions

1. Open `python-scrapper/.env` file

2. Add this line (or update if it already exists):
   ```env
   GROQ_API_KEY=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
   ```

3. Save the file

4. Restart your backend server

## What This Enables

With Groq configured, your LLM features will work:
- ✅ **Niche Classification** - Automatically categorizes business niches
- ✅ **Segment Naming** - AI-generated names for lead segments
- ✅ **Insights Generation** - Market insights and patterns
- ✅ **Custom Field Extraction** - Extract structured data from websites

## Verify It's Working

After restarting, create a new job and check the logs. You should see:
- No more "LLM call failed" warnings
- Niche classification working
- Segments with AI-generated names
- Insights generated for jobs

## Note

Groq is fast and free (with rate limits), making it perfect for:
- Real-time niche classification
- Quick segment naming
- Fast insights generation

The system will automatically use Groq if `GROQ_API_KEY` is set, otherwise it will try OpenAI or Anthropic if those are configured.


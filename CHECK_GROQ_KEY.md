# Fix: GROQ_API_KEY Not Being Loaded

## Problem

The test shows:
- `GROQ_API_KEY: NOT SET (0 chars)` ❌
- `OPENAI_API_KEY: SET (164 chars)` ✅

This means the factory is using OpenAI instead of Groq.

## Solution

### Step 1: Add GROQ_API_KEY to .env file

Open `python-scrapper/.env` and add:

```bash
GROQ_API_KEY=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
```

**Important:** 
- Make sure there are no spaces around the `=`
- Make sure the key is on its own line
- Don't wrap it in quotes unless the key itself contains special characters

### Step 2: Verify the key is loaded

After adding the key, restart your backend server and check the logs. You should see:

```
INFO:app.ai.factory:LLM Factory: GROQ_API_KEY=SET, OPENAI_API_KEY=SET, ANTHROPIC_API_KEY=NOT SET
INFO:app.ai.factory:LLM Factory: Using Groq provider
INFO:app.ai.factory:Creating GroqLLMClient with model: llama-3.1-70b-versatile
INFO:app.ai.llm_clients:GroqLLMClient initialized with base_url=https://api.groq.com/openai/v1
```

### Step 3: Test

Create a new job and watch the logs. You should see:

```
INFO:httpx:HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
```

Instead of:

```
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 401 Unauthorized"
```

## Why This Happens

The `.env` file might have:
1. Missing `GROQ_API_KEY` line
2. Wrong format (spaces, quotes, etc.)
3. Encoding issues (null characters - we saw this error earlier)

## Quick Fix Command

If you want to add it via command line (Windows PowerShell):

```powershell
Add-Content -Path ".env" -Value "GROQ_API_KEY=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"
```

Or manually edit the `.env` file and add the line above.

## After Fixing

1. **Restart the backend server** (the .env file is loaded at startup)
2. **Create a new job** to test
3. **Check logs** - should see Groq API calls, not OpenAI

The factory will now prioritize Groq when `GROQ_API_KEY` is set! 🎉


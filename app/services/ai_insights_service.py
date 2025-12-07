"""AI Insights service for generating job summaries and segments"""
import logging
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.orm import ScrapeJobORM, LeadORM
from app.ai.factory import create_llm_client

logger = logging.getLogger(__name__)


async def generate_job_ai_insights(
    db: Session,
    job_id: int,
    org_id: int
) -> None:
    """
    Generate AI insights (summary + segments) for a completed job.
    Updates job.ai_status, job.ai_summary, job.ai_segments, job.ai_error.
    """
    job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    # Mark as running and clear previous error
    job.ai_status = "running"
    job.ai_error = None
    db.commit()

    # Get leads (limit to 200 for prompt size)
    leads = (
        db.query(LeadORM)
        .filter(LeadORM.job_id == job_id)
        .limit(200)
        .all()
    )

    if not leads:
        job.ai_status = "error"
        job.ai_error = "No leads found for this job, nothing to summarize."
        db.commit()
        logger.warning(f"Job {job_id} has no leads for AI insights")
        return

    # Build simplified lead data for prompt
    simplified = []
    for lead in leads:
        simplified.append({
            "name": lead.name or "Unknown",
            "company": getattr(lead, "company", None),
            "website": lead.website,
            "country": lead.country,
            "city": lead.city,
            "niche": lead.niche,
            "emails": lead.emails or [],
            "phones": lead.phones or [],
            "tags": lead.tags or [],
            "quality_score": float(lead.quality_score) if lead.quality_score else None,
        })

    # Create prompt
    job_name = f"{job.niche}{' - ' + job.location if job.location else ''}"
    prompt = f"""You are analyzing scraped leads for a B2B outreach platform.

Job name: {job_name}
Total leads (sampled): {len(simplified)}

Each lead has: name, company, website, country, city, niche, emails, phones, tags, quality_score.

1. Give a short paragraph (2-4 sentences) summarizing WHAT kind of leads these are
   (niches, locations, company types, anything interesting patterns you notice).

2. Suggest 3-6 segments as JSON array.
   Each segment should have:
   - name: short descriptive name
   - description: what makes this segment unique
   - ideal_use_case: when to target this group (e.g., "Best for cold email campaigns", "Ideal for premium services")
   - rough_percentage_of_leads: estimated percentage (0-100)

Respond ONLY as valid JSON with this structure:
{{
  "summary": "text here",
  "segments": [
    {{
      "name": "...",
      "description": "...",
      "ideal_use_case": "...",
      "rough_percentage_of_leads": 40
    }}
  ]
}}
"""

    try:
        llm_client = create_llm_client()
        if not llm_client:
            job.ai_status = "disabled"
            job.ai_error = "No LLM API key configured. Configure GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in Settings to enable AI insights."
            db.commit()
            logger.warning(f"No LLM client available for job {job_id}")
            return

        # Call LLM
        system_message = {
            "role": "system",
            "content": "You are an analytics assistant for a lead scraping SaaS. Answer clearly and concisely. Always return valid JSON."
        }
        
        user_content = prompt + "\n\nLeads sample:\n" + json.dumps(simplified[:50], indent=2)
        user_message = {
            "role": "user",
            "content": user_content
        }

        # Request JSON format explicitly (if supported by provider)
        # Note: Groq may not support response_format, so we'll handle both cases
        try:
            response = await llm_client.chat_completion(
                [system_message, user_message], 
                temperature=0.7,
                response_format={"type": "json_object"}  # Force JSON output (OpenAI/Groq)
            )
        except Exception as format_error:
            # If response_format is not supported, try without it
            logger.warning(f"response_format not supported, retrying without it: {format_error}")
            response = await llm_client.chat_completion(
                [system_message, user_message], 
                temperature=0.7
            )
        
        # Parse response
        if not response:
            logger.error(f"LLM returned None/empty response for job {job_id}")
            raise ValueError("Empty response from LLM - check API key and model configuration")
        
        # Extract content (handle different response formats)
        if isinstance(response, str):
            content = response
        elif hasattr(response, "choices") and len(response.choices) > 0:
            content = response.choices[0].message.content
        elif isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
        else:
            logger.error(f"Unexpected response format: {type(response)}, response: {response}")
            raise ValueError(f"Unexpected response format: {type(response)}")
        
        if not content or not content.strip():
            logger.error(f"LLM returned empty content for job {job_id}, response type: {type(response)}")
            raise ValueError("Empty response from LLM - no content in response")
        
        logger.info(f"LLM response received for job {job_id}, content length: {len(content)}")

        # Try to extract JSON from response (might be wrapped in markdown code blocks)
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)

        # Validate structure
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
        
        summary = parsed.get("summary", "")
        segments = parsed.get("segments", [])
        
        if not isinstance(segments, list):
            raise ValueError("Segments must be a list")
        
        # Validate segments
        for seg in segments:
            if not isinstance(seg, dict):
                raise ValueError("Each segment must be a dict")
            if "name" not in seg:
                raise ValueError("Each segment must have a 'name' field")

        # Save to job
        job.ai_status = "ready"
        job.ai_summary = summary
        job.ai_segments = segments
        job.ai_error = None
        db.commit()
        
        logger.info(f"Successfully generated AI insights for job {job_id}: {len(segments)} segments")

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)[:200]}. Response was: {content[:500] if 'content' in locals() else 'N/A'}"
        logger.error(f"JSON decode error for job {job_id}: {e}")
        logger.error(f"Response content that failed to parse: {content[:1000] if 'content' in locals() else 'N/A'}")
        job.ai_status = "error"
        job.ai_error = error_msg
        db.commit()
    except ValueError as e:
        # Handle "Empty response from LLM" and other value errors
        error_msg = str(e)[:500]
        logger.error(f"Value error for job {job_id}: {e}")
        job.ai_status = "error"
        job.ai_error = error_msg
        db.commit()
    except Exception as e:
        error_msg = str(e)[:500]
        logger.exception(f"Failed to generate AI insights for job {job_id}: {e}")
        job.ai_status = "error"
        job.ai_error = error_msg
        db.commit()


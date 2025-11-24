"""AI QA / Anomaly detector for lead quality"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
import json

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class QADetector:
    """Service for detecting lead quality issues and anomalies"""
    
    @staticmethod
    def check_lead_quality(db: Session, lead_id: int) -> bool:
        """
        Run QA check on a lead
        
        Returns:
            True if check completed successfully
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return False
        
        # Build context
        context = {
            "name": lead.name or "",
            "niche": lead.niche or "",
            "address": lead.address or "",
            "city": lead.city or "",
            "country": lead.country or "",
            "emails": lead.emails or [],
            "phones": lead.phones or [],
            "website": lead.website or "",
            "services": lead.service_tags or [],
            "tech_stack": lead.tech_stack or {},
        }
        
        # Run QA check
        qa_result = QADetector._run_qa_check(context)
        
        # Update lead
        lead.qa_status = qa_result.get("qa_status", "review")
        lead.qa_reason = qa_result.get("qa_reason", "")
        db.commit()
        
        return True
    
    @staticmethod
    def _run_qa_check(context: Dict) -> Dict[str, str]:
        """Run AI QA check on lead context"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                # Fallback to rule-based check
                return QADetector._rule_based_qa(context)
            
            prompt = f"""You are checking if a scraped business lead looks valid and complete.

Data (JSON):
{json.dumps(context, ensure_ascii=False, indent=2)}

Decide:
- qa_status: "ok", "review", or "bad"
  * "ok": looks like a real business with reasonable data.
  * "review": something might be off or incomplete (missing key info, suspicious patterns).
  * "bad": clearly not a valid lead (spam, irrelevant, non-business, fake).

- qa_reason: short explanation (max 1 sentence).

Check for:
- Missing obvious contact details when website exists
- Country/city mismatches
- Too generic or non-business websites
- Suspicious patterns

Respond as pure JSON: {{"qa_status": "...", "qa_reason": "..."}}"""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.2))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.2)
            
            if result:
                try:
                    data = json.loads(result)
                    return {
                        "qa_status": data.get("qa_status", "review"),
                        "qa_reason": data.get("qa_reason", "AI check completed"),
                    }
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"AI QA check failed: {e}")
        
        # Fallback to rule-based
        return QADetector._rule_based_qa(context)
    
    @staticmethod
    def _rule_based_qa(context: Dict) -> Dict[str, str]:
        """Fallback rule-based QA check"""
        issues = []
        
        # Check for missing contact info
        if context.get("website") and not context.get("emails") and not context.get("phones"):
            issues.append("Missing contact information")
        
        # Check for suspicious patterns
        name = context.get("name", "").lower()
        if any(suspicious in name for suspicious in ["test", "example", "sample", "lorem"]):
            issues.append("Suspicious name pattern")
        
        # Check for country/city mismatch (basic)
        country = context.get("country", "").lower()
        city = context.get("city", "").lower()
        if country and city:
            # Basic validation (could be enhanced)
            if country == "uk" and "new york" in city:
                issues.append("Location mismatch")
        
        if issues:
            return {
                "qa_status": "review",
                "qa_reason": "; ".join(issues),
            }
        
        return {
            "qa_status": "ok",
            "qa_reason": "No obvious issues detected",
        }


"""Service package inference - extract productized offerings"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class ServicePackageInference:
    """Infer productized service packages from website content"""
    
    @staticmethod
    def infer_packages(
        db: Session,
        lead_id: int,
        website_text: Optional[str] = None
    ) -> List[Dict]:
        """
        Infer service packages from lead's website
        
        Returns:
            [
                {
                    "name": "Full mouth rehabilitation package",
                    "description": "...",
                    "services": ["implants", "crowns", "whitening"],
                    "confidence": 0.85
                },
                ...
            ]
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return []
        
        # Get website text if not provided
        if not website_text and lead.website:
            website_text = ServicePackageInference._fetch_website_text(lead.website)
        
        if not website_text:
            return []
        
        # Use LLM to infer packages
        packages = ServicePackageInference._infer_with_llm(lead, website_text)
        
        return packages
    
    @staticmethod
    def _infer_with_llm(lead: LeadORM, website_text: str) -> List[Dict]:
        """Infer packages using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return []
            
            prompt = f"""Analyze this business website and identify productized service packages or bundles.

Business: {lead.name or 'Unknown'}
Niche: {lead.niche or 'Unknown'}

Website content:
{website_text[:4000]}

Identify any service packages, bundles, or productized offerings mentioned. For example:
- "Full mouth rehabilitation package"
- "Emergency dental bundle"
- "Premium wellness package"
- "Basic cleaning + checkup"

For each package found, extract:
1. Package name
2. Brief description
3. Services included
4. Confidence (0-1)

Respond in JSON array format:
[
  {{
    "name": "Package name",
    "description": "What it includes",
    "services": ["service1", "service2"],
    "confidence": 0.85
  }}
]

If no packages are found, return empty array [].

Only extract packages that are explicitly mentioned or clearly implied."""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.3))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.3)
            
            if result:
                import json
                import re
                # Extract JSON array
                json_match = re.search(r'\[[^\]]+\]', result, re.DOTALL)
                if json_match:
                    packages = json.loads(json_match.group())
                    # Validate and filter by confidence
                    validated = []
                    for pkg in packages:
                        if isinstance(pkg, dict) and pkg.get("name"):
                            confidence = pkg.get("confidence", 0.5)
                            if confidence >= 0.5:  # Only include confident packages
                                validated.append({
                                    "name": pkg.get("name", ""),
                                    "description": pkg.get("description", ""),
                                    "services": pkg.get("services", []),
                                    "confidence": confidence,
                                })
                    return validated
            
        except Exception as e:
            logger.warning(f"LLM package inference failed: {e}")
        
        return []
    
    @staticmethod
    def _fetch_website_text(website: str) -> Optional[str]:
        """Fetch and extract text from website"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                response = client.get(website, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                # Remove script and style
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(separator=" ", strip=True)
                text = " ".join(text.split())
                return text[:8000]  # Limit length
        
        except Exception as e:
            logger.warning(f"Failed to fetch website text: {e}")
            return None


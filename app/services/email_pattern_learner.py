"""Email pattern learning service - learns patterns per domain"""
import logging
from typing import Dict, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.orm import LeadORM, OrganizationORM

logger = logging.getLogger(__name__)


class EmailPatternLearner:
    """Learn email patterns per domain from confirmed leads"""
    
    @staticmethod
    def extract_pattern(email: str, first_name: str, last_name: str) -> Optional[str]:
        """
        Extract email pattern from confirmed email
        
        Returns pattern like: "first.last", "f.last", "firstlast", etc.
        """
        if not email or not first_name or not last_name:
            return None
        
        email_lower = email.lower()
        first_lower = first_name.lower().strip()
        last_lower = last_name.lower().strip()
        domain = email_lower.split("@")[1] if "@" in email_lower else None
        
        if not domain:
            return None
        
        local_part = email_lower.split("@")[0]
        
        # Try to match common patterns
        patterns = [
            f"{first_lower}.{last_lower}",
            f"{first_lower[0]}.{last_lower}",
            f"{first_lower}{last_lower}",
            f"{first_lower[0]}{last_lower}",
            f"{first_lower}",
            f"{last_lower}",
            f"{last_lower}.{first_lower}",
            f"{first_lower}_{last_lower}",
            f"{first_lower[0]}{last_lower[0]}",
            f"{first_lower}-{last_lower}",
        ]
        
        for pattern in patterns:
            if local_part == pattern:
                return pattern
        
        return None
    
    @staticmethod
    def learn_from_leads(db: Session, organization_id: int, domain: Optional[str] = None) -> Dict[str, Dict]:
        """
        Learn email patterns from existing leads with confirmed emails
        
        Returns:
            Dict mapping domain -> pattern -> count
        """
        query = db.query(LeadORM).filter(
            LeadORM.organization_id == organization_id,
            LeadORM.emails.isnot(None),
        )
        
        if domain:
            query = query.filter(LeadORM.website.contains(domain))
        
        leads = query.all()
        
        pattern_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for lead in leads:
            if not lead.emails or not lead.name:
                continue
            
            # Extract first and last name
            name_parts = lead.name.split()
            if len(name_parts) < 2:
                continue
            
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:])
            
            # Extract domain from website or email
            lead_domain = None
            if lead.website:
                lead_domain = lead.website.replace("http://", "").replace("https://", "").split("/")[0]
            elif lead.emails:
                for email in lead.emails:
                    if "@" in email:
                        lead_domain = email.split("@")[1]
                        break
            
            if not lead_domain:
                continue
            
            # Extract pattern for each email
            for email in lead.emails:
                pattern = EmailPatternLearner.extract_pattern(email, first_name, last_name)
                if pattern:
                    pattern_counts[lead_domain][pattern] += 1
        
        # Convert to sorted format
        result = {}
        for domain, patterns in pattern_counts.items():
            sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
            result[domain] = {
                "patterns": [p[0] for p in sorted_patterns],
                "counts": {p[0]: p[1] for p in sorted_patterns},
            }
        
        return result
    
    @staticmethod
    def get_best_patterns_for_domain(
        db: Session,
        organization_id: int,
        domain: str,
        limit: int = 3
    ) -> List[str]:
        """
        Get best email patterns for a domain based on learned data
        
        Returns:
            List of pattern strings in order of preference
        """
        learned = EmailPatternLearner.learn_from_leads(db, organization_id, domain)
        
        if domain in learned:
            return learned[domain]["patterns"][:limit]
        
        # Return default patterns if no learning data
        return ["first.last", "f.last", "firstlast"]


def enhance_email_finder_with_learning(
    db: Session,
    organization_id: int,
    domain: str,
    first_name: str,
    last_name: str
) -> List[str]:
    """
    Enhance email finder candidates with learned patterns
    
    Returns:
        Enhanced list of email candidates (learned patterns first)
    """
    from app.services.email_finder import generate_candidates
    
    # Get learned patterns
    learner = EmailPatternLearner()
    learned_patterns = learner.get_best_patterns_for_domain(db, organization_id, domain)
    
    # Generate default candidates
    default_candidates = generate_candidates(first_name, last_name, domain)
    
    # Reorder: learned patterns first, then defaults
    enhanced = []
    seen = set()
    
    # Add learned patterns first (if they match)
    for pattern in learned_patterns:
        # Convert pattern to email
        f = first_name.lower().strip()
        l = last_name.lower().strip()
        fi = f[0] if f else ""
        
        email = None
        if pattern == "first.last":
            email = f"{f}.{l}@{domain}"
        elif pattern == "f.last":
            email = f"{fi}.{l}@{domain}"
        elif pattern == "firstlast":
            email = f"{f}{l}@{domain}"
        elif pattern == "flast":
            email = f"{fi}{l}@{domain}"
        
        if email and email not in seen:
            enhanced.append(email)
            seen.add(email)
    
    # Add remaining default candidates
    for candidate in default_candidates:
        if candidate not in seen:
            enhanced.append(candidate)
            seen.add(candidate)
    
    return enhanced


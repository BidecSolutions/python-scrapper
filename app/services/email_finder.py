"""Email finder service - generate and verify email candidates"""
import logging
from dataclasses import dataclass
from typing import Optional, List
from app.services.email_verifier import verify_email, VerificationStatus

logger = logging.getLogger(__name__)


@dataclass
class EmailCandidateResult:
    """Result of email finding attempt"""
    email: str
    status: VerificationStatus
    reason: str
    score: float


def generate_candidates(first_name: str, last_name: str, domain: str) -> List[str]:
    """
    Generate email candidate patterns
    
    Common patterns:
    - first.last@domain
    - f.last@domain
    - firstlast@domain
    - flast@domain
    - first@domain
    - last@domain
    - last.first@domain
    """
    f = first_name.lower().strip()
    l = last_name.lower().strip()
    
    if not f or not l:
        return []
    
    fi = f[0] if f else ""
    li = l[0] if l else ""
    
    candidates = [
        f"{f}.{l}@{domain}",           # john.doe@example.com
        f"{fi}.{l}@{domain}",          # j.doe@example.com
        f"{f}{l}@{domain}",            # johndoe@example.com
        f"{fi}{l}@{domain}",           # jdoe@example.com
        f"{f}@{domain}",               # john@example.com
        f"{l}@{domain}",               # doe@example.com
        f"{l}.{f}@{domain}",           # doe.john@example.com
        f"{f}_{l}@{domain}",           # john_doe@example.com
        f"{fi}{li}@{domain}",          # jd@example.com
        f"{f}-{l}@{domain}",           # john-doe@example.com
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    
    return unique


def score_candidate(status: VerificationStatus, reason: str) -> float:
    """
    Score an email candidate based on verification status
    
    Returns:
        Score between 0.0 and 1.0
    """
    if status == VerificationStatus.VALID:
        return 0.95
    if status == VerificationStatus.RISKY:
        return 0.7
    if status == VerificationStatus.UNKNOWN:
        return 0.4
    if status == VerificationStatus.DISPOSABLE:
        return 0.1
    if status == VerificationStatus.GIBBERISH:
        return 0.1
    if status == VerificationStatus.INVALID:
        return 0.0
    
    return 0.0


def find_email(
    first_name: str,
    last_name: str,
    domain: str,
    skip_smtp: bool = False,
    min_confidence: float = 0.3
) -> Optional[EmailCandidateResult]:
    """
    Find email address for a person
    
    Args:
        first_name: First name
        last_name: Last name
        domain: Company domain
        skip_smtp: Skip SMTP verification (faster but less accurate)
        min_confidence: Minimum confidence score to return (0.0-1.0)
    
    Returns:
        EmailCandidateResult if found, None otherwise
    """
    if not first_name or not last_name or not domain:
        return None
    
    domain = domain.lower().strip().lstrip("@")
    
    candidates = generate_candidates(first_name, last_name, domain)
    
    if not candidates:
        return None
    
    best: Optional[EmailCandidateResult] = None
    
    for email in candidates:
        try:
            status, reason = verify_email(email, skip_smtp=skip_smtp)
            score = score_candidate(status, reason)
            
            candidate_result = EmailCandidateResult(
                email=email,
                status=status,
                reason=reason,
                score=score,
            )
            
            if best is None or candidate_result.score > best.score:
                best = candidate_result
            
            # Short-circuit if we find a very strong one
            if status == VerificationStatus.VALID and score >= 0.9:
                logger.info(f"Found high-confidence email: {email}")
                break
                
        except Exception as e:
            logger.warning(f"Error verifying candidate {email}: {e}")
            continue
    
    # Apply minimum confidence threshold
    if best and best.score < min_confidence:
        logger.debug(f"Best candidate {best.email} has low confidence {best.score}")
        return None
    
    return best


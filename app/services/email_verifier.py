"""Email verification service - DNS + SMTP checking"""
import re
import socket
import smtplib
import logging
from enum import Enum
from typing import Tuple, List, Optional
from functools import lru_cache

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False
    logging.warning("dnspython not installed. Install with: pip install dnspython")

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class VerificationStatus(str, Enum):
    """Email verification status"""
    VALID = "valid"
    INVALID = "invalid"
    RISKY = "risky"
    UNKNOWN = "unknown"
    DISPOSABLE = "disposable"
    GIBBERISH = "gibberish"


# Common disposable email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "tempmail.com",
    "guerrillamail.com",
    "throwaway.email",
    "temp-mail.org",
    "getnada.com",
    "mohmal.com",
    "fakeinbox.com",
    "trashmail.com",
}


def is_gibberish(local_part: str) -> bool:
    """Check if local part looks like gibberish"""
    if not local_part:
        return True
    
    numbers = sum(ch.isdigit() for ch in local_part)
    letters = sum(ch.isalpha() for ch in local_part)
    
    if letters == 0:
        return True
    
    if numbers > letters * 2:
        return True
    
    if len(local_part) > 30:
        return True
    
    # Check for random character patterns
    if re.match(r'^[a-z]{1,2}\d{4,}', local_part.lower()):
        return True
    
    return False


def validate_syntax(email: str) -> bool:
    """Basic email syntax validation"""
    return EMAIL_REGEX.match(email) is not None


@lru_cache(maxsize=1000)
def lookup_mx(domain: str) -> Tuple[List[str], bool]:
    """
    Lookup MX records for a domain
    
    Returns:
        (mx_hosts, found) - list of MX hosts and whether records were found
    """
    if not HAS_DNS:
        return [], False
    
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_hosts = [str(r.exchange).rstrip(".") for r in answers]
        # Sort by priority (lower is better)
        mx_hosts.sort()
        return mx_hosts, True
    except dns.resolver.NXDOMAIN:
        logger.debug(f"Domain {domain} does not exist")
        return [], False
    except dns.resolver.NoAnswer:
        logger.debug(f"No MX records for {domain}")
        return [], False
    except Exception as e:
        logger.warning(f"DNS lookup error for {domain}: {e}")
        return [], False


def smtp_check(email: str, mx_hosts: List[str], timeout: int = 8) -> Tuple[bool, bool]:
    """
    Check if email is accepted by SMTP server
    
    Args:
        email: Email address to check
        mx_hosts: List of MX hostnames
        timeout: Connection timeout in seconds
    
    Returns:
        (accepted, is_catch_all_guess) - whether email is accepted and if it's likely catch-all
    """
    if not mx_hosts:
        return False, True
    
    local_domain = "example.com"  # Replace with your domain if you have one
    
    for host in mx_hosts[:3]:  # Try first 3 MX hosts
        try:
            server = smtplib.SMTP(host, 25, timeout=timeout)
            server.set_debuglevel(0)
            
            server.helo(local_domain)
            server.mail(f"test@{local_domain}")
            code, msg = server.rcpt(email)
            server.quit()
            
            if 200 <= code < 300:
                # Accepted - could be valid or catch-all
                return True, False
            elif 500 <= code < 600:
                # Hard reject - definitely invalid
                return False, False
            else:
                # Other response - inconclusive
                continue
                
        except socket.timeout:
            logger.debug(f"SMTP timeout for {host}")
            continue
        except smtplib.SMTPException as e:
            logger.debug(f"SMTP error for {host}: {e}")
            continue
        except OSError as e:
            logger.debug(f"Connection error for {host}: {e}")
            continue
        except Exception as e:
            logger.debug(f"Unexpected error checking {host}: {e}")
            continue
    
    # Couldn't confirm - might be catch-all or server blocking
    return False, True


def verify_email(email: str, skip_smtp: bool = False) -> Tuple[VerificationStatus, str]:
    """
    Verify an email address
    
    Args:
        email: Email address to verify
        skip_smtp: If True, skip SMTP check (faster but less accurate)
    
    Returns:
        (status, reason) - verification status and reason
    """
    email = email.strip().lower()
    
    # Syntax check
    if not validate_syntax(email):
        return VerificationStatus.INVALID, "invalid_syntax"
    
    local, _, domain = email.partition("@")
    
    if not local or not domain:
        return VerificationStatus.INVALID, "invalid_format"
    
    # Check disposable domains
    if domain in DISPOSABLE_DOMAINS:
        return VerificationStatus.DISPOSABLE, "disposable_domain"
    
    # Check for gibberish
    if is_gibberish(local):
        return VerificationStatus.GIBBERISH, "gibberish_local_part"
    
    # DNS MX lookup
    mx_hosts, found = lookup_mx(domain)
    if not found:
        return VerificationStatus.INVALID, "no_mx_records"
    
    if not mx_hosts:
        return VerificationStatus.INVALID, "no_mx_records"
    
    # SMTP check (if not skipped)
    if skip_smtp:
        return VerificationStatus.UNKNOWN, "smtp_skipped"
    
    accepted, catch_all_guess = smtp_check(email, mx_hosts)
    
    if accepted:
        if catch_all_guess:
            return VerificationStatus.RISKY, "accepted_catch_all"
        return VerificationStatus.VALID, "smtp_accepted"
    else:
        # Couldn't determine - many servers hide this
        return VerificationStatus.UNKNOWN, "smtp_inconclusive"


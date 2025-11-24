"""Contact information extractor"""
import re
from bs4 import BeautifulSoup
from typing import Tuple, Set
from app.utils.text import normalize_email, normalize_phone


EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE
)

PHONE_REGEX = re.compile(
    r"""
    (?:(?:\+?\d{1,3}[\s\-]?)?      # country code
    (?:\(?\d{2,4}\)?[\s\-]?)?      # area code
    \d{3,4}[\s\-]?\d{3,4})         # local number
    """,
    re.VERBOSE
)

# Additional phone patterns for better coverage
PHONE_PATTERNS = [
    re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
    re.compile(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),  # US format
    re.compile(r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}'),  # US format with parentheses
]


def extract_contacts(html: str) -> Tuple[Set[str], Set[str]]:
    """Extract email addresses and phone numbers from HTML text"""
    # Extract emails
    emails = set()
    for match in EMAIL_REGEX.findall(html):
        normalized = normalize_email(match)
        if len(normalized) > 5:  # Basic validation
            emails.add(normalized)
    
    # Extract phones
    phones = set()
    for pattern in [PHONE_REGEX] + PHONE_PATTERNS:
        for match in pattern.findall(html):
            normalized = normalize_phone(match)
            # Filter out very short numbers (likely false positives)
            if len(normalized) >= 7:
                phones.add(normalized)
    
    # Also check mailto: links and tel: links
    mailto_pattern = re.compile(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
    for match in mailto_pattern.findall(html):
        normalized = normalize_email(match)
        emails.add(normalized)
    
    tel_pattern = re.compile(r'tel:([+\d\s\-\(\)]+)', re.IGNORECASE)
    for match in tel_pattern.findall(html):
        normalized = normalize_phone(match.replace('tel:', ''))
        if len(normalized) >= 7:
            phones.add(normalized)
    
    return emails, phones


def extract_from_soup(soup: BeautifulSoup) -> Tuple[Set[str], Set[str]]:
    """Extract contacts from BeautifulSoup object"""
    # Get all text content
    text = soup.get_text(" ", strip=True)
    
    # Also check href attributes for mailto: and tel: links
    href_text = ""
    for tag in soup.find_all(['a', 'link'], href=True):
        href = tag.get('href', '')
        href_text += " " + href
    
    combined_text = text + " " + href_text
    return extract_contacts(combined_text)


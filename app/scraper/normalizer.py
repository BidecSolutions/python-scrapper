"""Data normalization utilities"""
from typing import List
from app.utils.text import normalize_email, normalize_phone


def normalize_emails(emails: List[str]) -> List[str]:
    """Normalize list of email addresses"""
    normalized = set()
    for email in emails:
        normalized.add(normalize_email(email))
    return sorted(list(normalized))


def normalize_phones(phones: List[str]) -> List[str]:
    """Normalize list of phone numbers"""
    normalized = set()
    for phone in phones:
        normalized.add(normalize_phone(phone))
    return sorted(list(normalized))


"""Text processing utilities"""
import re


def normalize_email(email: str) -> str:
    """Normalize email address"""
    return email.lower().strip()


def normalize_phone(phone: str) -> str:
    """Normalize phone number"""
    # Remove common separators
    phone = re.sub(r'[\s\-\(\)\.]', '', phone)
    return phone.strip()


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


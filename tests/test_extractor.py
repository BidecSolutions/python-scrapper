"""Tests for contact extractor"""
import pytest
from bs4 import BeautifulSoup
from app.scraper.extractor import extract_contacts, extract_from_soup


def test_extract_email():
    """Test email extraction"""
    html = """
    <html>
        <body>
            <p>Contact us at info@example.com</p>
            <a href="mailto:support@example.com">Email us</a>
        </body>
    </html>
    """
    emails, phones = extract_contacts(html)
    assert "info@example.com" in emails
    assert "support@example.com" in emails


def test_extract_phone():
    """Test phone number extraction"""
    html = """
    <html>
        <body>
            <p>Call us at +1-555-123-4567</p>
            <a href="tel:+923001234567">Call</a>
            <p>Or (555) 987-6543</p>
        </body>
    </html>
    """
    emails, phones = extract_contacts(html)
    assert len(phones) > 0
    # Check that we found phone numbers
    phone_str = " ".join(phones)
    assert "555" in phone_str or "123" in phone_str


def test_extract_from_soup():
    """Test extraction from BeautifulSoup"""
    html = """
    <html>
        <body>
            <p>Email: contact@test.com</p>
            <p>Phone: +1-555-1234</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    emails, phones = extract_from_soup(soup)
    assert "contact@test.com" in emails
    assert len(phones) > 0


"""Geographic utilities"""
from typing import Optional, Tuple


def parse_location(location: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse location string into city and country
    Simple implementation - can be enhanced
    """
    parts = location.split(",")
    if len(parts) >= 2:
        city = parts[0].strip()
        country = parts[-1].strip()
        return city, country
    return location.strip(), None


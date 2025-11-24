"""Pre-configured site templates for common scraping targets"""
from typing import Dict, Any

# ⚠️ LEGAL WARNING: Only use these configs on sites that explicitly allow scraping
# Always check robots.txt and Terms of Service before using

SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
    # Example template - DO NOT USE ON ACTUAL SITES WITHOUT PERMISSION
    "example-doctors": {
        "url": "https://example-doctors.com",
        "search_box_selector": "input[name='search']",
        "submit_selector": "button.search-submit",
        "result_item_selector": ".doctor-card",
        "fields": {
            "name": ".doctor-name",
            "specialty": ".doctor-specialty",
            "phone": ".doctor-phone",
            "address": ".doctor-address"
        },
        "profile_link_selector": ".doctor-name a",
        "wait_seconds": 5,
        "requires_interaction": True,
    },
    
    # Add more site configs here as needed
    # Always include legal disclaimer in description
}

def get_site_config(site_key: str) -> Dict[str, Any]:
    """Get site configuration by key"""
    return SITE_CONFIGS.get(site_key)

def list_available_sites() -> list:
    """List all available site configuration keys"""
    return list(SITE_CONFIGS.keys())


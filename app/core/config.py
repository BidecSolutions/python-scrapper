"""Configuration settings"""
import os
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    import os
    # Try to load .env, but handle errors gracefully
    try:
        load_dotenv()
    except (ValueError, UnicodeDecodeError) as e:
        # If .env has issues (null chars, encoding), try to load it manually
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            # Only set if not already in environment
                            if key and key not in os.environ:
                                os.environ[key] = value
            except Exception:
                pass  # If manual load fails, just use system env vars
except ImportError:
    pass  # python-dotenv not installed, use system env vars


class Settings:
    """Application settings loaded from environment variables"""
    
    # API Keys
    GOOGLE_PLACES_API_KEY: Optional[str] = os.getenv("GOOGLE_PLACES_API_KEY")
    GOOGLE_SEARCH_API_KEY: Optional[str] = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_CX: Optional[str] = os.getenv("GOOGLE_SEARCH_CX")
    BING_SEARCH_API_KEY: Optional[str] = os.getenv("BING_SEARCH_API_KEY")
    SERPAPI_KEY: Optional[str] = os.getenv("SERPAPI_KEY")
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    
    # Geocoding API Keys
    OPENCAGE_API_KEY: Optional[str] = os.getenv("OPENCAGE_API_KEY")
    GOOGLE_GEOCODING_API_KEY: Optional[str] = os.getenv("GOOGLE_GEOCODING_API_KEY")
    
    # Database (defaults to SQLite for easy setup)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./lead_scraper.db"
    )
    
    # Scraping settings
    DEFAULT_MAX_PAGES: int = int(os.getenv("DEFAULT_MAX_PAGES", "5"))
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "15"))
    DEFAULT_CONCURRENCY: int = int(os.getenv("DEFAULT_CONCURRENCY", "5"))
    
    # Rate limiting
    REQUESTS_PER_MINUTE: int = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
    
    # User agent
    USER_AGENT: str = os.getenv("USER_AGENT", "LeadScraperBot/0.1")
    
    # JWT Secret Key (change in production!)
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-secret-key-change-in-production-min-32-chars-please-use-a-secure-random-string"
    )


settings = Settings()


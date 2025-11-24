"""HTTP utilities for making requests"""
import time
import logging
import requests
from typing import Optional
from collections import deque
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter using sliding window"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()
    
    def wait_if_needed(self):
        """Wait if we've hit the rate limit"""
        now = time.time()
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                # Clean up again after sleep
                now = time.time()
                while self.request_times and self.request_times[0] < now - 60:
                    self.request_times.popleft()
        
        self.request_times.append(time.time())


_rate_limiter = RateLimiter(settings.REQUESTS_PER_MINUTE)


def get_session() -> requests.Session:
    """Get a configured requests session"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return session


def make_request(url: str, **kwargs) -> Optional[requests.Response]:
    """Make a rate-limited HTTP request"""
    _rate_limiter.wait_if_needed()
    
    session = kwargs.pop("session", None) or get_session()
    timeout = kwargs.pop("timeout", settings.DEFAULT_TIMEOUT)
    
    try:
        response = session.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None


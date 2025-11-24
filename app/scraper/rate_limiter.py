"""Rate limiting utilities"""
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """Simple rate limiter using sliding window"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: deque[float] = deque()
    
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


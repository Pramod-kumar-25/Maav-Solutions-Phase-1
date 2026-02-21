import time
import asyncio
from typing import Dict, List
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class InMemoryRateLimiter:
    def __init__(self):
        self.points: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()

    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Sliding window rate limiter core.
        Returns True if limited, False otherwise.
        """
        try:
            now = time.time()
            async with self.lock:
                if key in self.points:
                    # Clean expired timestamps
                    valid_points = [t for t in self.points[key] if now - t < window_seconds]
                    if not valid_points:
                        del self.points[key]
                    else:
                        self.points[key] = valid_points
                else:
                    self.points[key] = []
                    
                if len(self.points[key]) >= max_requests:
                    return True
                
                self.points[key].append(now)
                return False
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return False  # Fail-open behavior

limiter = InMemoryRateLimiter()

async def check_rate_limit(key: str, max_requests: int, window_seconds: int):
    """
    Throws generic 429 if the rate limit is exceeded.
    Does not expose limit headers.
    """
    if await limiter.is_rate_limited(key, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

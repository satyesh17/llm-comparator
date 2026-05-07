"""Retry helpers for handling rate-limited API calls."""

import random
import time
from typing import Callable, TypeVar

from google.api_core import exceptions as google_exceptions

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    max_attempts: int = 4,
    base_delay: float = 1.0,
) -> T:
    """Call fn() with retry on rate-limit errors.
    
    - Honors API-supplied retry_delay when available (Gemini's ResourceExhausted)
    - Falls back to exponential backoff with jitter
    - Only retries on rate-limit errors; other failures propagate
    """
    for attempt in range(max_attempts):
        try:
            return fn()
        
        except google_exceptions.ResourceExhausted as e:
            if attempt == max_attempts - 1:
                raise  # last attempt — give up
            
            # Try to honor API's retry_delay hint
            wait = _extract_retry_delay(e)
            if wait is None:
                # Fall back to exponential backoff with jitter
                wait = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
            
            print(f"  ⏳ Rate limited. Waiting {wait:.1f}s before retry {attempt + 2}/{max_attempts}...")
            time.sleep(wait)
    
    # Should be unreachable, but keep the type checker happy
    raise RuntimeError("retry_with_backoff: exhausted all attempts")


def _extract_retry_delay(exc: google_exceptions.ResourceExhausted) -> float | None:
    """Pull retry_delay (seconds) out of Gemini's exception, if present."""
    # The ResourceExhausted exception's metadata sometimes contains a RetryInfo
    for detail in getattr(exc, "_details", []) or []:
        if hasattr(detail, "retry_delay"):
            delay = detail.retry_delay
            if hasattr(delay, "seconds"):
                return float(delay.seconds) + 1.0  # add 1s safety margin
    return None
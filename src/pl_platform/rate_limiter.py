"""Token bucket rate limiter for HTTP clients."""

import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket rate limiter.

    Holds up to `capacity` tokens. Each call to `acquire()` consumes one
    token. Tokens regenerate at `refill_rate` per second. If no token is
    available, `acquire()` blocks (sleeps) until one is.

    The `clock` and `sleep` parameters allow injection of fake versions
    for testing — they default to real time functions in production.

    Example:
        # 10 requests per minute = 10/60 tokens per second
        bucket = TokenBucket(capacity=10, refill_rate=10/60)
        for _ in range(15):
            bucket.acquire()  # first 10 instant, next 5 wait ~6s each
    """

    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self._clock = clock
        self._sleep = sleep
        self._last_refill = clock()

    def acquire(self) -> None:
        """Block until a token is available, then consume one."""
        while True:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return
            wait = (1 - self.tokens) / self.refill_rate
            logger.debug("Bucket empty, sleeping %.2fs", wait)
            self._sleep(wait)

    def _refill(self) -> None:
        """Add tokens based on time elapsed since last refill."""
        now = self._clock()
        elapsed = now - self._last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self._last_refill = now
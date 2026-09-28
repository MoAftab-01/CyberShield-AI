"""In-process rate limiting.

Free-tier hosting means a single instance and no Redis, so the counter lives in
process memory. That is a real limitation and worth stating plainly rather than
hiding: with more than one worker each process keeps its own count, so the
effective limit is ``limit * workers``, and a restart clears it. It is still
worth having, because the endpoint it protects spends a metered third-party
quota (Groq) per call, and the alternative on this tier is nothing at all.

A sliding window of timestamps is used instead of a fixed window: a fixed
window lets a caller spend the whole allowance at the end of one window and
again at the start of the next, which is exactly the burst the limit exists to
prevent.
"""

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Allow at most ``max_requests`` per ``window_seconds``, per key."""

    def __init__(self, max_requests: int, window_seconds: float):

        self.max_requests = max_requests
        self.window_seconds = window_seconds

        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, float]:
        """Record an attempt.

        Returns ``(allowed, retry_after_seconds)``. ``retry_after`` is zero
        when the attempt is allowed.
        """

        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:

            hits = self._hits[key]

            while hits and hits[0] < cutoff:
                hits.popleft()

            if len(hits) >= self.max_requests:
                return False, max(0.0, hits[0] + self.window_seconds - now)

            hits.append(now)

            return True, 0.0

    def prune(self) -> None:
        """Drop keys with no recent activity.

        Without this the dictionary grows once per distinct user for the
        lifetime of the process, which on a long-running instance is a slow
        leak.
        """

        cutoff = time.monotonic() - self.window_seconds

        with self._lock:
            for key in [
                key
                for key, hits in self._hits.items()
                if not hits or hits[-1] < cutoff
            ]:
                del self._hits[key]

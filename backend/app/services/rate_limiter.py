import threading
import time

from app.infra.settings import settings


class FixedWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._state: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            window_start, count = self._state.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start = now
                count = 0
            if count >= self.limit:
                self._state[key] = (window_start, count)
                return False
            self._state[key] = (window_start, count + 1)
            return True


rate_limiter = FixedWindowRateLimiter(settings.rate_limit_per_minute)

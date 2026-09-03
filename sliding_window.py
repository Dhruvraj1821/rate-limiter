import time
from collections import deque

class SlidingWindowCounter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = {}

    def allow(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        q = self.requests.setdefault(client_id, deque())

        while q and q[0] < window_start:
            q.popleft()

        if len(q) < self.limit:
            q.append(now)
            return True
        return False
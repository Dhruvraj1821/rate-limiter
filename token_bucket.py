import time

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}

    def allow(self, client_id: str) -> bool:
        now = time.time()
        tokens, last_refill = self.buckets.get(client_id, (self.capacity, now))

        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens >= 1:
            tokens -= 1
            self.buckets[client_id] = (tokens, now)
            return True
        else:
            self.buckets[client_id] = (tokens, now)
            return False
import time
from redis_client import r

CAPACITY = 5
REFILL_RATE = 1

def allow(client_id: str) -> bool:
    key = f"bucket:{client_id}"
    now = time.time()
    data = r.hgetall(key)

    if data:
        tokens = float(data["tokens"])
        last_refill = float(data["last_refill"])
    else:
        tokens = CAPACITY
        last_refill = now

    elapsed = now - last_refill
    tokens = min(CAPACITY, tokens + elapsed * REFILL_RATE)

    if tokens >= 1:
        tokens -= 1
        allowed = True
    else:
        allowed = False

    r.hset(key, mapping={"tokens": tokens, "last_refill": now})
    return allowed
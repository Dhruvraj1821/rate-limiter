import time
from redis_client import r

CAPACITY = 5
REFILL_RATE = 1

with open("token_bucket.lua") as f:
    SCRIPT = f.read()

check_script = r.register_script(SCRIPT)

def allow(client_id: str) -> bool:
    key = f"bucket:{client_id}"
    result = check_script(keys=[key], args=[CAPACITY, REFILL_RATE, time.time()])
    return bool(result)
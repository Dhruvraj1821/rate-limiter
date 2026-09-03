from fastapi import FastAPI
from pydantic import BaseModel
from token_bucket import TokenBucket
from sliding_window import SlidingWindowCounter

app = FastAPI()

token_bucket_limiter = TokenBucket(capacity=5, refill_rate=1)

sliding_window_limiter = SlidingWindowCounter(limit=5, window_seconds=10)

STRATEGY = "sliding_window"

class CheckRequest(BaseModel):
    client_id: str

class CheckResponse(BaseModel):
    allowed: bool


@app.get("/health")
def health_check():
    return {"status" : "ok"}

@app.post("/check", response_model=CheckResponse)
def check_rate_limit(request: CheckRequest):
    if STRATEGY == "token_bucket":
        allowed = token_bucket_limiter.allow(request.client_id)
    else:
        allowed = sliding_window_limiter.allow(request.client_id)
    return CheckResponse(allowed=allowed)
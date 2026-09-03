from fastapi import FastAPI, Header, HTTPException, Depends
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from token_bucket import TokenBucket
from sliding_window import SlidingWindowCounter
from redis_token_bucket import allow as redis_token_bucket_allow

load_dotenv()

app = FastAPI()

VALID_API_KEY = os.getenv("API_KEY")
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

token_bucket_limiter = TokenBucket(capacity=5, refill_rate=1)

sliding_window_limiter = SlidingWindowCounter(limit=5, window_seconds=10)

STRATEGY = "redis_token_bucket"

class CheckRequest(BaseModel):
    client_id: str

class CheckResponse(BaseModel):
    allowed: bool


@app.get("/health")
def health_check():
    return {"status" : "ok"}

@app.post("/check", response_model=CheckResponse)
def check_rate_limit(request: CheckRequest, _: None = Depends(verify_api_key)):
    if STRATEGY == "token_bucket":
        allowed = token_bucket_limiter.allow(request.client_id)
    elif STRATEGY == "sliding_window":
        allowed = sliding_window_limiter.allow(request.client_id)
    else:
        allowed = redis_token_bucket_allow(request.client_id)
    return CheckResponse(allowed=allowed)
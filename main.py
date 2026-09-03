from fastapi import FastAPI
from pydantic import BaseModel
from token_bucket import TokenBucket

app = FastAPI()

limiter = TokenBucket(capacity=5, refill_rate=1)

class CheckRequest(BaseModel):
    client_id: str

class CheckResponse(BaseModel):
    allowed: bool


@app.get("/health")
def health_check():
    return {"status" : "ok"}

@app.post("/check", response_model=CheckResponse)
def check_rate_limit(request: CheckRequest):
    allowed = limiter.allow(request.client_id)
    return CheckResponse(allowed=allowed)
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class CheckRequest(BaseModel):
    client_id: str

class CheckResponse(BaseModel):
    allowed: bool


@app.get("/health")
def health_check():
    return {"status" : "ok"}

@app.post("/check", response_model=CheckResponse)
def check_rate_limit(request: CheckRequest):
    return CheckResponse(allowed=True)
# Distributed Rate Limiter

A rate limiting service built with FastAPI and Redis, designed to demonstrate correct handling of shared state across multiple service instances — including a real concurrency bug found during development, fixed with an atomic Lua script.

## Problem

Rate limiting exists to protect a service from being overwhelmed — by a single misbehaving client, a traffic spike, or abuse. The interesting engineering problem isn't the algorithm itself; it's that in any real deployment you run *multiple instances* of your service behind a load balancer for reliability. If each instance tracks rate limits in its own local memory, a client can get a full quota from instance A and another full quota from instance B — the limit becomes fiction the moment you scale past one process. Solving this requires shared, consistent state across all instances, updated safely even when multiple requests arrive at the same time.

## Live demo

**https://rate-limiter-mr74.onrender.com**

- `GET /health` — basic liveness check
- `POST /check` — rate limit check, requires an `X-API-Key` header

Note: this runs on Render's free tier, which spins down after 15 minutes of inactivity. The first request after idle time may take 30–60 seconds to respond while the instance wakes up — this is a hosting limitation, not a bug in the service.

## Algorithms implemented

The rate limiting strategy is configurable via a `STRATEGY` variable, so multiple approaches coexist in the codebase rather than replacing one another.

- **Token bucket** — each client has a bucket of tokens that refill steadily over time up to a capacity. Requests spend a token; if none are available, the request is denied. This design allows clients to burst above their steady-state rate without penalty, as long as they have saved-up capacity — useful for APIs where occasional bursts are legitimate and shouldn't be punished the same as sustained abuse.
- **Sliding window counter** — tracks the actual timestamps of recent requests and only allows a new one if fewer than the limit occurred within the trailing window. Unlike token bucket, there's no banked "credit" to spend in a burst — this gives a strict, hard cap, appropriate for sensitive endpoints like login or password-reset where burst tolerance just makes abuse easier.

## The concurrency bug I found and fixed

The first Redis-backed implementation of token bucket read the current token count (`HGETALL`), computed the new value in Python, then wrote it back (`HSET`) — two separate network round trips with a gap in between. That gap is a race condition:

1. Request A reads `tokens = 1`
2. Request B reads `tokens = 1` (A hasn't written back yet)
3. Request A computes `0`, writes it, returns `allowed = True`
4. Request B computes `0` from its own stale read, writes it, also returns `allowed = True`

Both requests get approved even though only one token existed. This is a classic read-modify-write race — the same pattern that breaks bank balance updates, inventory counts, and seat reservations anywhere shared state is touched by multiple processes without coordination.

**Fix:** move the entire check-and-decrement into a Lua script executed atomically on the Redis server via `EVALSHA`. Redis guarantees no other command can interleave while a script runs, closing the gap entirely — the read, compute, and write happen as one indivisible step.

**Proof:** a test using `concurrent.futures.ThreadPoolExecutor` fires 20 simultaneous requests at a bucket with capacity 5.
- Against the naive two-step version: intermittently allows 6, 7, or more requests — the race is timing-dependent, so it doesn't fail every run, which is itself part of what makes this class of bug dangerous in production.
- Against the Lua-script version: consistently allows exactly 5, every run.

## Architecture

```
Client
  │
  ▼
FastAPI instance(s)  ──►  Redis (Upstash, managed)
  │                              │
  └── API key auth        atomic Lua script
      (header check)       (token bucket logic)
```

Multiple FastAPI instances can run concurrently (proven directly by running two local instances on different ports and confirming they share one correct rate limit total, not one limit each). All instances talk to the same Redis instance, so there is exactly one source of truth for each client's remaining tokens. In production, Redis is a managed Upstash database rather than a local container — the app never manages the Redis server itself, only holds a connection URL to it.

## Failure handling

If Redis becomes unreachable — a network blip, an outage — the service doesn't just return a 500 for every request. Failure mode is configurable:

- **Fail open**: let requests through, prioritizing availability over strict enforcement. Appropriate when the service being protected matters more than never exceeding the limit briefly.
- **Fail closed**: deny requests, prioritizing strict enforcement over availability. Appropriate for sensitive endpoints where being unprotected is worse than being briefly unavailable.

This is a deliberate design decision rather than an oversight — different endpoints in a real system might reasonably choose different defaults.

## Load test results

Using Locust, simulating concurrent users hitting `/check`:

| Metric | Value |
|---|---|
| Total requests | 13,381 |
| Failures | 0 |
| Requests/sec | 714 |
| Median latency | 15 ms |
| p95 latency | 49 ms |
| p99 latency | 57 ms |

Zero failures under sustained concurrent load is the practical confirmation that the atomic Lua fix holds up outside of the targeted 20-request race-condition test — not just correct in a unit test, but correct under real throughput.

## How to run it locally

**Requirements:** Python 3.x, Docker Desktop (for Redis)

```bash
# start Redis
docker run -d -p 6379:6379 --name rate-limiter-redis redis

# set up the app
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# create a .env file with:
# API_KEY=your-local-secret-key

uvicorn main:app --reload
```

Test it:
```bash
curl -X POST http://127.0.0.1:8000/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-local-secret-key" \
  -d '{"client_id": "test-user"}'
```

Run the test suite:
```bash
pytest
```
from token_bucket import TokenBucket

def test_allows_up_to_capacity():
    bucket = TokenBucket(capacity=3, refill_rate=0)
    assert bucket.allow("a") is True
    assert bucket.allow("a") is True
    assert bucket.allow("a") is True
    assert bucket.allow("a") is False
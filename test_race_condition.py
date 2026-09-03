import concurrent.futures
import redis_token_bucket

def fire_request(_):
    return redis_token_bucket.allow("race_test_client")

def test_no_race_condition_with_lua():
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fire_request, range(20)))
    assert results.count(True) == 5
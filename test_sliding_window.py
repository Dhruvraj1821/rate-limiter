import time
from sliding_window import SlidingWindowCounter

def test_allows_up_to_limit_then_resets_after_window():
    window = SlidingWindowCounter(limit=2, window_seconds=1)
    assert window.allow("a") is True
    assert window.allow("a") is True
    assert window.allow("a") is False  

    time.sleep(1.1) 
    assert window.allow("a") is True 
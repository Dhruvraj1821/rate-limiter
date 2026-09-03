import time
from sliding_window import SlidingWindowCounter

def test_allows_up_to_limit_then_resets_after_window():
    window = SlidingWindowCounter(limit=2, window_seconds=1)
    assert window.allow("a") is True
    assert window.allow("a") is True
    assert window.allow("a") is False  # limit hit

    time.sleep(1.1)  # wait for the window to fully expire
    assert window.allow("a") is True  # allowed again
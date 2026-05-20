"""Tests for the token bucket rate limiter."""

from pl_platform.rate_limiter import TokenBucket


def make_fake_time():
    """Create fake clock and sleep functions that share advancing state.

    Returns (clock, sleep, state) where state is a dict with:
    - state["time"]: current fake time (float, seconds)
    - state["sleeps"]: list of sleep durations called

    fake_sleep advances state["time"] by the sleep duration — simulating
    that time passed during the sleep.
    """
    state = {"time": 0.0, "sleeps": []}

    def fake_clock():
        return state["time"]

    def fake_sleep(duration):
        state["sleeps"].append(duration)
        state["time"] += duration

    return fake_clock, fake_sleep, state


def test_burst_within_capacity_does_not_sleep():
    """First `capacity` acquires happen instantly without sleeping."""
    clock, sleep, state = make_fake_time()
    bucket = TokenBucket(capacity=10, refill_rate=10 / 60, clock=clock, sleep=sleep)

    for _ in range(10):
        bucket.acquire()

    assert state["sleeps"] == []


def test_acquire_beyond_capacity_sleeps():
    """The 11th acquire on a 10-capacity bucket sleeps until a token refills."""
    clock, sleep, state = make_fake_time()
    bucket = TokenBucket(capacity=10, refill_rate=10 / 60, clock=clock, sleep=sleep)

    # Drain the bucket
    for _ in range(10):
        bucket.acquire()

    # 11th: bucket empty, should sleep ~6 seconds (1 / (10/60))
    bucket.acquire()

    assert len(state["sleeps"]) == 1
    assert 5.9 < state["sleeps"][0] < 6.1


def test_bucket_refills_after_time_passes():
    """After enough fake time passes, the bucket refills to allow new acquires."""
    clock, sleep, state = make_fake_time()
    bucket = TokenBucket(capacity=10, refill_rate=10 / 60, clock=clock, sleep=sleep)

    # Drain the bucket
    for _ in range(10):
        bucket.acquire()

    # Advance time by 60 seconds (full refill window)
    state["time"] = 60.0

    # Should be able to acquire 10 more without sleeping
    for _ in range(10):
        bucket.acquire()

    assert state["sleeps"] == []


def test_tokens_capped_at_capacity():
    """Bucket doesn't accumulate more than `capacity` tokens, even after long idle."""
    clock, sleep, state = make_fake_time()
    bucket = TokenBucket(capacity=10, refill_rate=10 / 60, clock=clock, sleep=sleep)

    # No acquires; advance time by 10 minutes (would generate 100 tokens uncapped)
    state["time"] = 600.0

    # Should still only allow `capacity` (10) before sleeping
    for _ in range(10):
        bucket.acquire()

    # 11th must sleep
    bucket.acquire()

    assert len(state["sleeps"]) == 1
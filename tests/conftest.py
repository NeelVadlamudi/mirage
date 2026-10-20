import pytest

from agent.ratelimit import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Each test starts with empty rate-limit counters."""
    limiter.reset()
    yield
    limiter.reset()

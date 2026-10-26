import pytest
from jobsearch.security import check_api_key, AuthError, RateLimiter, RateLimitError

def test_key_ok_and_bad():
    check_api_key("abc", "abc")
    for bad in (None, "", "abd"):
        with pytest.raises(AuthError):
            check_api_key(bad, "abc")

def test_no_server_key(monkeypatch):
    monkeypatch.delenv("JOBSEARCH_API_KEY", raising=False)
    with pytest.raises(AuthError):
        check_api_key("x")

def test_env_key(monkeypatch):
    monkeypatch.setenv("JOBSEARCH_API_KEY", "k1")
    check_api_key("k1")

def test_rate_limit_window():
    t = [0.0]
    rl = RateLimiter(2, 10, clock=lambda: t[0])
    rl.hit("a"); rl.hit("a")
    with pytest.raises(RateLimitError):
        rl.hit("a")
    rl.hit("b")
    t[0] = 11
    rl.hit("a")

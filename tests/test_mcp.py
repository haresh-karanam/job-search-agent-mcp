import asyncio, os, pytest
from jobsearch import mcp_server as m
from jobsearch.security import RateLimiter

def test_six_tools_registered():
    names = {t.name for t in asyncio.run(m.mcp.list_tools())}
    assert names == {"search_jobs", "get_job", "extract_skills", "score_match", "compare_jobs", "skill_gap"}

def test_call_tool():
    res = asyncio.run(m.mcp.call_tool("get_job", {"job_id": "J002"}))
    assert "J002" in str(res)

def test_rate_limit_applies():
    old = m.limiter
    m.limiter = RateLimiter(1, 60)
    try:
        m._guard("x")
        with pytest.raises(RuntimeError):
            m._guard("x")
    finally:
        m.limiter = old

def test_main_rejects_bad_key(monkeypatch):
    monkeypatch.setenv("JOBSEARCH_API_KEY", "a")
    monkeypatch.setenv("JOBSEARCH_CLIENT_KEY", "b")
    with pytest.raises(SystemExit):
        m.main()

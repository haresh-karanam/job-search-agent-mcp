import asyncio
from fastapi.testclient import TestClient
from jobsearch import agent
from jobsearch.api import app, limiter

def test_parse_filters():
    f = agent.parse({"request": "Machine learning internship in Leeds over 25k"})["filters"]
    assert f == {"query": "machine learning", "location": "leeds", "job_type": "internship", "min_salary": 25000}

def test_run_returns_ranked():
    r = agent.run("data analyst internship in London", ["python", "sql"])
    scores = [s["score"] for s in r["scores"]]
    assert scores == sorted(scores, reverse=True) and len(r["jobs"]) <= 5

def test_no_match_message():
    r = agent.run("data analyst graduate role in London over 99k", [])
    assert "No adverts matched" in r["answer"]

def test_api(monkeypatch):
    monkeypatch.setenv("JOBSEARCH_API_KEY", "secret")
    limiter._hits.clear()
    c = TestClient(app)
    assert c.get("/health").json() == {"ok": True}
    assert c.post("/ask", json={"request": "data analyst internship"}).status_code == 401
    h = {"x-api-key": "secret"}
    ok = c.post("/ask", json={"request": "data analyst internship in London", "my_skills": ["python"]}, headers=h)
    assert ok.status_code == 200 and "answer" in ok.json()
    assert c.post("/ask", json={"request": "x"}, headers=h).status_code == 422
    assert c.post("/tools/get_job", json={"job_id": "J001"}, headers=h).json()["result"]["id"] == "J001"
    assert c.post("/tools/nope", json={}, headers=h).status_code == 404
    assert c.post("/tools/get_job", json={"bad": 1}, headers=h).status_code == 422

def test_api_rate_limit(monkeypatch):
    monkeypatch.setenv("JOBSEARCH_API_KEY", "secret")
    limiter._hits.clear()
    c = TestClient(app)
    codes = [c.post("/tools/get_job", json={"job_id": "J001"}, headers={"x-api-key": "secret"}).status_code
             for _ in range(61)]
    assert codes[-1] == 429 and codes[0] == 200
    limiter._hits.clear()


def test_rate_limit_is_per_client_not_per_key(monkeypatch):
    monkeypatch.setenv("JOBSEARCH_API_KEY", "secret")
    limiter._hits.clear()
    c = TestClient(app)
    codes = [c.post("/tools/get_job", json={"job_id": "J001"}, headers={"x-api-key": f"wrong{i}"}).status_code
             for i in range(61)]
    assert codes[0] == 401 and codes[-1] == 429      # guessing different keys is still limited
    limiter._hits.clear()

def test_input_limits(monkeypatch):
    monkeypatch.setenv("JOBSEARCH_API_KEY", "secret")
    limiter._hits.clear()
    c = TestClient(app); h = {"x-api-key": "secret"}
    assert c.post("/ask", json={"request": "x" * 600}, headers=h).status_code == 422
    assert c.post("/ask", json={"request": "data analyst", "my_skills": ["a"] * 51}, headers=h).status_code == 422
    limiter._hits.clear()

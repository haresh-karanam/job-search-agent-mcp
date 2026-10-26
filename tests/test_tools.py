from jobsearch import tools as T, store

def test_search_filters():
    r = T.search_jobs("data", location="London", job_type="internship", min_salary=22000, limit=50)
    assert r and all("london" in j["location"].lower() and j["type"] == "internship" for j in r)

def test_search_limit_bounds():
    assert len(T.search_jobs(limit=500)) <= 50
    assert len(T.search_jobs(limit=0)) == 1

def test_get_job():
    assert T.get_job("j001")["id"] == "J001"
    assert "error" in T.get_job("nope")

def test_extract_skills():
    assert {"python", "sql"} <= set(T.extract_skills("I use Python, SQL and git."))

def test_score_match_and_missing():
    j = store.get("J001")
    r = T.score_match("J001", j["skills"][:2])
    assert 0 < r["score"] < 1 and r["missing"]
    assert T.score_match("J001", j["skills"])["score"] == 1.0
    assert "error" in T.score_match("X", [])

def test_compare_sorted():
    rows = T.compare_jobs(["J001", "J002", "J003", "BAD"], ["python", "sql"])
    scores = [r["score"] for r in rows if "error" not in r]
    assert scores == sorted(scores, reverse=True) and "error" in rows[-1]

def test_skill_gap():
    g = T.skill_gap(["python"], top=3)
    assert len(g["missing"]) == 3 and all(m["skill"] != "python" for m in g["missing"])
    assert T.skill_gap(["python"], job_type="internship")["adverts_considered"] < 80

def test_skill_demand():
    assert store.skill_demand(top=3)

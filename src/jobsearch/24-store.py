"""Job store: loads adverts from JSON and answers simple queries."""
from __future__ import annotations
import json, os
from collections import Counter
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent / "data" / "sample_jobs.json"


@lru_cache(maxsize=8)
def _load(resolved: str, mtime: float) -> tuple[dict, ...]:
    return tuple(json.loads(Path(resolved).read_text(encoding="utf-8")))


def load_jobs(path: str | None = None) -> tuple[dict, ...]:
    """Load adverts from `path`, else $JOBSEARCH_DATA, else the bundled synthetic sample."""
    p = Path(path or os.environ.get("JOBSEARCH_DATA") or DATA)
    return _load(str(p), p.stat().st_mtime)


def search(query: str = "", location: str = "", job_type: str = "",
           min_salary: int = 0, limit: int = 10, path: str | None = None) -> list[dict]:
    words = [w for w in query.lower().split() if w]
    out = []
    for j in load_jobs(path):
        hay = (j["title"] + " " + j["description"] + " " + " ".join(j["skills"])).lower()
        if words and not all(w in hay for w in words):
            continue
        if location and location.lower() not in j["location"].lower():
            continue
        if job_type and job_type.lower() != j["type"]:
            continue
        if j["salary_gbp"] < min_salary:
            continue
        out.append(j)
    return out[: max(1, min(limit, 50))]


def get(job_id: str, path: str | None = None) -> dict | None:
    for j in load_jobs(path):
        if j["id"].lower() == job_id.lower():
            return j
    return None


def skill_demand(path: str | None = None, top: int = 10) -> list[tuple[str, int]]:
    c = Counter(s for j in load_jobs(path) for s in j["skills"])
    return c.most_common(top)

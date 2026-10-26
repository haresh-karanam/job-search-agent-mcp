"""MCP server (stdio). Set JOBSEARCH_API_KEY before starting.

The key is checked at start-up against JOBSEARCH_CLIENT_KEY (the key the client config
holds), and every tool call goes through the rate limiter.
"""
from __future__ import annotations
import os, sys
from mcp.server.fastmcp import FastMCP
from . import tools as T
from .security import RateLimiter, check_api_key, AuthError, RateLimitError

mcp = FastMCP("job-search")
limiter = RateLimiter(max_calls=int(os.environ.get("JOBSEARCH_RATE_LIMIT", "60")), per_seconds=60)


def _guard(name: str):
    try:
        limiter.hit("stdio-client")
    except RateLimitError as e:
        raise RuntimeError(str(e))


@mcp.tool()
def search_jobs(query: str = "", location: str = "", job_type: str = "",
                min_salary: int = 0, limit: int = 10) -> list[dict]:
    """Search job adverts by keywords, location, job_type (internship/graduate), min salary."""
    _guard("search_jobs"); return T.search_jobs(query, location, job_type, min_salary, limit)


@mcp.tool()
def get_job(job_id: str) -> dict:
    """Get one advert by id, for example J001."""
    _guard("get_job"); return T.get_job(job_id)


@mcp.tool()
def extract_skills(text: str) -> list[str]:
    """Find known skills in a block of text."""
    _guard("extract_skills"); return T.extract_skills(text)


@mcp.tool()
def score_match(job_id: str, my_skills: list[str]) -> dict:
    """Score how well a skill list matches one advert."""
    _guard("score_match"); return T.score_match(job_id, my_skills)


@mcp.tool()
def compare_jobs(job_ids: list[str], my_skills: list[str]) -> list[dict]:
    """Rank several adverts against a skill list."""
    _guard("compare_jobs"); return T.compare_jobs(job_ids, my_skills)


@mcp.tool()
def skill_gap(my_skills: list[str], job_type: str = "", top: int = 8) -> dict:
    """Most requested skills you are missing."""
    _guard("skill_gap"); return T.skill_gap(my_skills, job_type, top)


def main() -> None:
    try:
        check_api_key(os.environ.get("JOBSEARCH_CLIENT_KEY"))
    except AuthError as e:
        print(f"auth failed: {e}", file=sys.stderr)
        sys.exit(1)
    mcp.run()


if __name__ == "__main__":
    main()

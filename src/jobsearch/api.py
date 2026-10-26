"""FastAPI wrapper with API-key auth and rate limiting.

Run locally only: uvicorn jobsearch.api:app --host 127.0.0.1
There is no TLS or user system here. Do not expose it to the internet as it is.
"""
from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException, Request
from typing import Annotated
from pydantic import BaseModel, Field
from . import agent, tools as T
from .security import AuthError, RateLimitError, RateLimiter, check_api_key

app = FastAPI(title="Job search agent", version="0.1.0")
limiter = RateLimiter(max_calls=60, per_seconds=60)


def _auth(key: str | None, request: Request):
    """Rate limit by client address BEFORE checking the key, so wrong-key guessing is limited too."""
    try:
        limiter.hit(request.client.host if request.client else "unknown")
        check_api_key(key)
    except AuthError as e:
        raise HTTPException(401, str(e))
    except RateLimitError as e:
        raise HTTPException(429, str(e))


class AskBody(BaseModel):
    request: str = Field(min_length=3, max_length=500)
    my_skills: list[Annotated[str, Field(max_length=40)]] = Field(default_factory=list, max_length=50)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ask")
def ask(body: AskBody, request: Request, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key, request)
    r = agent.run(body.request, body.my_skills)
    return {"answer": r["answer"], "filters": r["filters"], "seconds": round(r["seconds"], 4)}


@app.post("/tools/{name}")
def call_tool(name: str, args: dict, request: Request, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key, request)
    if name not in T.TOOLS:
        raise HTTPException(404, "unknown tool")
    try:
        return {"result": T.TOOLS[name](**args)}
    except (TypeError, ValueError):
        raise HTTPException(422, "invalid arguments")

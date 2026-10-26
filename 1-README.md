# Job Search Agent with MCP Server

A Python job search assistant with an MCP server, a LangGraph agent and a FastAPI service.

## What this is, and what it is not (read first)

This is a **rebuild**. The original project was lost, so this version was written again from its description, with AI assistance. Nothing here recovers the original.

| Part | Status |
| --- | --- |
| Six tools, MCP server, FastAPI service, LangGraph agent | Built, tested, runs offline |
| **Default demo mode** | Rule-based parser, **80 synthetic (made-up) adverts**, **no LLM**. Fast and free, but it is a demo. |
| Import your own adverts (CSV/JSON) | Built and tested |
| LLM mode (any OpenAI-compatible endpoint, e.g. a local Ollama server) | Adapter written and **tested only against a fake HTTP server**. **Never run against a real model.** |
| Dockerfile | Written, **never built** (no Docker where this was made) |

The demo numbers are **not** evidence about LLM quality or real job matching:

- "30/30 benchmark" only means the rule parser handles 30 sentences written by the author, on made-up data.
- Run times of about 1 ms and a cost of $0 are because no model is called and the data is tiny.

If you mention this project, say it was rebuilt, uses synthetic demo data by default, and that LLM mode is untested until you run it yourself.

## Quick start on a Mac (offline demo, works with no accounts)

Python 3.10 or newer is needed (`python3 --version`). In Terminal, in this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python -m pytest --cov=src/jobsearch          # 46 tests
python -m jobsearch.agent "data analyst internship in London over 22k"
python scripts/run_benchmark.py                # offline demo check
python scripts/mcp_client_demo.py              # starts the MCP server and calls it
```

## Use your own job data

Export adverts to CSV or JSON (columns such as title, company, location, salary, description, skills, url; see the top of `src/jobsearch/ingest.py` for accepted names).

```bash
python -m jobsearch.ingest my_jobs.csv data/my_jobs.json
export JOBSEARCH_DATA=data/my_jobs.json
python -m jobsearch.agent "junior data analyst in Manchester"
```

The importer cleans text, drops duplicates and rows without a title or company, reads salaries like "£25,000" or "25k", finds skills in the description if there is no skills column, and flags adverts that look like they contain instructions for an AI (`injection_suspected`). Respect each job site's terms before you scrape or copy adverts; this package does not scrape anything.

## LLM mode (optional, you must set it up)

Any OpenAI-compatible chat endpoint works. A free local example is Ollama (`ollama serve`, then `ollama pull <model>`, which downloads a model of several GB, so it is not done for you).

```bash
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=<the model you pulled>
export LLM_API_KEY=<only if your endpoint needs one>   # read from the environment, never logged
python -m jobsearch.agent "machine learning internship in Cambridge"
```

What the LLM does: turns the request into filters (checked against a strict schema; if the reply is invalid or the call fails, the rule parser is used instead) and writes a two-sentence note about the top matches. It has no tools and cannot change anything.

To measure it: `python scripts/run_llm_benchmark.py` shows the plan; add `--yes` to run (30 calls, or 60 with `--explain`; one shared limit, `LLM_MAX_CALLS`, default 60). A paid endpoint costs real money; the script prints token usage; cost is reported as "unknown" unless you give your provider's prices. Results go to `benchmarks/results_llm.json`.

## Security notes

- **Untrusted job text.** Advert text is cleaned (control and zero-width characters removed, length capped), flagged if it looks like instructions, wrapped in `<untrusted>` tags with look-alike tags removed before any LLM sees it, and flagged adverts are never sent to the LLM. The LLM output is shown as text or validated as filters; it is never run. This reduces the risk; it does not remove it. Keep the LLM tool-free.
- **API key.** No default key. If `JOBSEARCH_API_KEY` is not set, the API rejects every request and the MCP server will not start. Keys are compared in constant time and never logged. `.env` is git-ignored.
- **Rate limiting** is per client address and applies before the key check, so guessing keys is limited too. It is in memory and per process.
- **Exposure.** Run the API on `127.0.0.1` only: `uvicorn jobsearch.api:app --host 127.0.0.1 --port 8000`. There is no TLS or user system. Do not put it on the internet as it is.
- **MCP over stdio** has no headers, so the key is checked once at start-up (`JOBSEARCH_CLIENT_KEY` must equal `JOBSEARCH_API_KEY`). Tool inputs are length-capped.
- Docker image runs as root and has not been built; harden before real use.

## MCP client config

```json
{
  "mcpServers": {
    "job-search": {
      "command": "/ABSOLUTE/PATH/.venv/bin/python",
      "args": ["-m", "jobsearch.mcp_server"],
      "env": {"PYTHONPATH": "/ABSOLUTE/PATH/src",
              "JOBSEARCH_API_KEY": "your-key", "JOBSEARCH_CLIENT_KEY": "your-key"}
    }
  }
}
```

## API example

```bash
export JOBSEARCH_API_KEY=choose-a-long-random-key
uvicorn jobsearch.api:app --host 127.0.0.1 --port 8000
curl -X POST localhost:8000/ask -H "x-api-key: $JOBSEARCH_API_KEY" -H "content-type: application/json" \
  -d '{"request":"graduate role in Leeds","my_skills":["python","sql"]}'
```

## How it works

```
request -> parse (rules, or LLM + schema check) -> search -> score (4 threads) -> rank -> summarise (+ optional LLM note)
```

Six tools: `search_jobs`, `get_job`, `extract_skills`, `score_match`, `compare_jobs`, `skill_gap`.
Code: `store.py` (data), `tools.py`, `agent.py` (LangGraph), `api.py`, `mcp_server.py`, `security.py`, `sanitize.py`, `ingest.py`, `llm.py`.

## Tested vs untested

| Tested here (offline) | Not tested |
| --- | --- |
| 46 unit tests, 96% line coverage | Any real LLM, local or hosted |
| MCP server started over stdio and called by a real MCP client | Claude Desktop or another MCP app |
| FastAPI app including auth, limits, bad input | Docker build and run |
| LLM adapter and agent against a fake HTTP server and fake callables | Accuracy with real adverts |
| CSV/JSON import including messy rows | Very large files, non-UK data |

## Limits

- The rule parser knows a fixed list of roles and UK cities.
- Matching is skill overlap only, with no semantic understanding.
- No scraping, no live job feeds.

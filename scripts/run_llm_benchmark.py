"""Run the 30 benchmark tasks through YOUR LLM endpoint. Needs LLM_BASE_URL and LLM_MODEL.

    export LLM_BASE_URL=http://localhost:11434/v1   # example: local Ollama (free)
    export LLM_MODEL=<model you have pulled>
    export LLM_API_KEY=...                          # only if the endpoint needs one
    python scripts/run_llm_benchmark.py          # shows the plan and stops
    python scripts/run_llm_benchmark.py --yes    # makes the calls

Safety: nothing is called without --yes. One shared limit (LLM_MAX_CALLS, default 60) covers every
call in the run. At most 30 calls, or 60 with --explain. A paid endpoint costs real money; check its price first. Optional cost
estimate (otherwise cost is reported as unknown): set LLM_PRICE_IN_PER_1M and LLM_PRICE_OUT_PER_1M (your provider's prices).

Status: NOT run against a real model by the author of this package. The adapter is tested
against a fake HTTP server only. Results are written to benchmarks/results_llm.json.
"""
import json, os, statistics, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from jobsearch import agent
from jobsearch.llm import CallBudget, LLMBudgetError, LLMClient, LLMConfigError
from run_benchmark import check

def run_task(t, llm, explain):
    if explain:
        res = agent.run(t["request"], t["my_skills"], llm=llm)
        return res, False
    res = agent.run(t["request"], t["my_skills"])        # rule parser, offline
    try:                                                  # then replace the filters with the LLM's
        f = agent.llm_parse(llm, t["request"])
    except LLMBudgetError:
        raise
    except Exception:
        return res, True                                  # LLM reply unusable: keep the rule result
    from jobsearch import tools as T
    res["filters"] = f
    res["jobs"] = T.search_jobs(f["query"], f["location"], f["job_type"], f["min_salary"], 20)
    return res, False


def main():
    explain = "--explain" in sys.argv
    limit = int(os.environ.get("LLM_MAX_CALLS", "60"))
    budget = CallBudget(limit)
    try:
        llm = LLMClient.from_env(budget=budget)
    except LLMConfigError as e:
        print("LLM not configured:", e); return 2
    print(f"Model {llm.model}. Up to {60 if explain else 30} calls, hard limit {limit} (LLM_MAX_CALLS).")
    if "--yes" not in sys.argv:
        print("Nothing was called. Add --yes to run."); return 0
    tasks = json.loads((ROOT / "benchmarks" / "tasks.json").read_text())
    rows, fallbacks, stopped = [], 0, False
    for t in tasks:
        try:
            res, fell_back = run_task(t, llm, explain)
        except LLMBudgetError:
            stopped = True
            break
        fallbacks += fell_back
        ok, why = check(t, res)
        rows.append({"id": t["id"], "pass": ok, "why": why, "used_rule_fallback": fell_back})
    u = llm.usage
    pin, pout = os.environ.get("LLM_PRICE_IN_PER_1M"), os.environ.get("LLM_PRICE_OUT_PER_1M")
    cost = ((u["prompt_tokens"] * float(pin) + u["completion_tokens"] * float(pout)) / 1e6) if pin and pout else None
    out = {"model": llm.model, "tasks_run": len(rows), "passed": sum(r["pass"] for r in rows), "total": len(tasks),
           "stopped_early_at_call_limit": stopped, "tasks_where_rule_fallback_was_used": fallbacks,
           "calls_used": budget.used, "usage": u,
           "estimated_cost": cost if cost is not None else "unknown (no prices set: LLM_PRICE_IN_PER_1M and LLM_PRICE_OUT_PER_1M)",
           "failures": [r for r in rows if not r["pass"]]}
    (ROOT / "benchmarks" / "results_llm.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)); return 0


if __name__ == "__main__":
    sys.exit(main())

"""OFFLINE DEMO CHECK of the rule-based agent. Not an LLM benchmark (see run_llm_benchmark.py).

A task passes when (1) the parser picked up the location, job type and salary in the
request and (2) every returned advert respects those filters. Cost is 0 because no
paid model is called. Results are printed and written to benchmarks/results.json.
"""
import json, statistics, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from jobsearch import agent, tools as T

def check(task, res):
    e, f = task["expect"], res["filters"]
    if f["location"] != e["location"].split()[0].lower() or f["job_type"] != e["job_type"] \
       or f["min_salary"] != e["min_salary"]:
        return False, f"filters {f}"
    for j in res["jobs"]:
        if e["location"] not in j["location"].lower():
            return False, f"{j['id']} wrong city"
        if e["job_type"] and j["type"] != e["job_type"]:
            return False, f"{j['id']} wrong type"
        if j["salary_gbp"] < e["min_salary"]:
            return False, f"{j['id']} low salary"
    return True, ""

def main(repeat=1):
    tasks = json.loads((ROOT / "benchmarks" / "tasks.json").read_text())
    rows, lat = [], []
    for t in tasks:
        for _ in range(repeat):
            res = agent.run(t["request"], t["my_skills"])
            ok, why = check(t, res)
            lat.append(res["seconds"] * 1000)
        rows.append({"id": t["id"], "request": t["request"], "pass": ok, "why": why,
                     "results": len(res["jobs"])})
    lat.sort()
    p95 = lat[int(0.95 * (len(lat) - 1))]
    out = {"passed": sum(r["pass"] for r in rows), "total": len(rows),
           "latency_ms_median": round(statistics.median(lat), 2), "latency_ms_p95": round(p95, 2),
           "cost_usd_per_run": 0.0, "failures": [r for r in rows if not r["pass"]],
           "kind": "OFFLINE DEMO CHECK. Rule-based parser, synthetic adverts, no LLM. Not evidence of LLM or real-world quality.", "note": "Cost is 0 because no model is called."}
    (ROOT / "benchmarks" / "results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "note"}, indent=1))
    return out

if __name__ == "__main__":
    main()

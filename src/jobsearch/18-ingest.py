"""Import your own adverts from CSV or JSON into the format the tools use.

    python -m jobsearch.ingest my_jobs.csv data/my_jobs.json
    export JOBSEARCH_DATA=data/my_jobs.json     # the tools and agent now use your file

Columns are matched by name, case-insensitive. Accepted names:
  title (required): title, job title, role, position
  company (required): company, employer, organisation, organization
  location: location, city, place
  salary: salary, salary_gbp, pay, annual salary (parses "£25,000", "25k", "24k-28k" -> lower bound)
  description: description, summary, details
  skills: skills, requirements (split on ; or ,). If missing, skills are found in the description.
  url: url, link
Rows without a title or company are skipped and counted. Duplicates (title+company+location) are dropped.
Text is cleaned and adverts that look like they contain instructions for an AI are flagged
(`injection_suspected`), not silently trusted.
"""
from __future__ import annotations
import csv, hashlib, json, re, sys
from pathlib import Path
from .sanitize import clean_text, looks_injected
from .skills import SKILL_VOCAB

ALIASES = {
    "title": ["title", "job title", "role", "position"],
    "company": ["company", "employer", "organisation", "organization"],
    "location": ["location", "city", "place"],
    "salary": ["salary", "salary_gbp", "pay", "annual salary"],
    "description": ["description", "summary", "details"],
    "skills": ["skills", "requirements"],
    "url": ["url", "link"],
}
MAX_ROWS = 20000


def parse_salary(raw: object) -> int:
    s = str(raw or "").lower().replace(",", "").replace("£", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k)?", s)
    if not m:
        return 0
    v = float(m.group(1)) * (1000 if m.group(2) else 1)
    return int(v) if 1000 <= v <= 1_000_000 else 0


def find_skills(text: str) -> list[str]:
    low = f" {text.lower()} "
    return sorted(s for s in SKILL_VOCAB
                  if re.search(rf"(?<![a-z0-9+#]){re.escape(s)}(?![a-z0-9+#])", low))


def _pick(row: dict, field: str) -> str:
    lower = {k.strip().lower(): v for k, v in row.items() if k}
    for a in ALIASES[field]:
        if lower.get(a):
            return str(lower[a])
    return ""


def normalise(rows: list[dict]) -> tuple[list[dict], dict]:
    out, seen, stats = [], set(), {"read": len(rows), "skipped_missing": 0, "duplicates": 0, "flagged": 0}
    for row in rows[:MAX_ROWS]:
        title, company = clean_text(_pick(row, "title"), 120), clean_text(_pick(row, "company"), 120)
        if not title or not company:
            stats["skipped_missing"] += 1
            continue
        loc = clean_text(_pick(row, "location"), 80)
        key = (title.lower(), company.lower(), loc.lower())
        if key in seen:
            stats["duplicates"] += 1
            continue
        seen.add(key)
        desc = clean_text(_pick(row, "description"))
        raw_sk = _pick(row, "skills")
        skills = sorted({clean_text(s, 40).lower() for s in re.split(r"[;,]", raw_sk) if s.strip()}) \
            or find_skills(f"{title}. {desc}")
        flagged = looks_injected(f"{title} {desc} {raw_sk}")
        stats["flagged"] += flagged
        low = title.lower()
        out.append({
            "id": "U" + hashlib.sha1("|".join(key).encode()).hexdigest()[:8].upper(),
            "title": title, "company": company, "location": loc or "Unknown",
            "salary_gbp": parse_salary(_pick(row, "salary")),
            "type": "internship" if any(w in low for w in ("intern", "placement")) else "graduate",
            "skills": skills, "description": desc, "url": clean_text(_pick(row, "url"), 300),
            "synthetic": False, "injection_suspected": flagged,
        })
    return out, stats


def read_rows(path: str) -> list[dict]:
    p = Path(path)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of adverts")
        return [r for r in data if isinstance(r, dict)]
    with p.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m jobsearch.ingest INPUT.(csv|json) OUTPUT.json")
        return 2
    jobs, stats = normalise(read_rows(argv[0]))
    Path(argv[1]).write_text(json.dumps(jobs, indent=1), encoding="utf-8")
    print(f"wrote {len(jobs)} adverts to {argv[1]}  {stats}")
    return 0 if jobs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

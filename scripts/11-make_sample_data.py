"""Generate data/sample_jobs.json: 80 SYNTHETIC job adverts (fixed seed).

These are made-up adverts for testing the tools. They are not real vacancies.
"""
import json, random
from pathlib import Path

random.seed(7)
titles = ["Data Analyst Intern", "Data Science Intern", "Machine Learning Intern",
          "Junior Data Analyst", "Graduate Data Scientist", "BI Analyst Intern",
          "AI Engineer Intern", "Data Engineer Intern", "Research Data Analyst",
          "Analytics Placement Student"]
companies = ["Northbridge Analytics", "Fenwick Labs", "Alder Retail", "Kestrel Health",
             "Marlow Energy", "Quayside Finance", "Brightwater Logistics", "Oakham Media",
             "Hollin Systems", "Tarn Software", "Westgate Insurance", "Linden Robotics"]
cities = ["London", "Manchester", "Cambridge", "Leeds", "Bristol", "Edinburgh", "Birmingham", "Remote (UK)"]
skills = ["python", "sql", "pandas", "numpy", "scikit-learn", "tableau", "power bi", "excel",
          "pytorch", "tensorflow", "docker", "git", "fastapi", "aws", "spark", "statistics",
          "langchain", "rag", "nlp", "airflow", "dbt", "r"]
jobs = []
for i in range(80):
    t = random.choice(titles)
    n = random.randint(4, 7)
    s = random.sample(skills, n)
    if "python" not in s and random.random() < .7:
        s[0] = "python"
    if "sql" not in s and random.random() < .6:
        s[1] = "sql"
    s = sorted(set(s))
    intern = "Intern" in t or "Placement" in t
    base = 22000 if intern else 29000
    sal = base + random.randint(0, 8) * 1000
    jobs.append({
        "id": f"J{i+1:03d}", "title": t, "company": random.choice(companies),
        "location": random.choice(cities), "salary_gbp": sal,
        "type": "internship" if intern else "graduate",
        "skills": s,
        "description": f"{t} working with {', '.join(s[:3])} on analytics projects. "
                       f"You will clean data, build reports and present findings to the team.",
        "synthetic": True,
    })
Path(__file__).resolve().parent.parent.joinpath("data", "sample_jobs.json").write_text(
    json.dumps(jobs, indent=1))
print(len(jobs), "jobs written")

"""Write benchmarks/tasks.json: 30 request tasks with machine-checkable expectations."""
import json, itertools
from pathlib import Path
roles = ["data analyst", "machine learning", "data engineer", "bi analyst", "ai engineer"]
cities = ["London", "Manchester", "Cambridge", "Leeds", "Bristol", "Edinburgh"]
tasks = []
i = 0
for role, city in itertools.product(roles, cities):
    i += 1
    kind = ["internship", "graduate", ""][i % 3]
    word = {"internship": "internship", "graduate": "graduate role", "": "job"}[kind]
    sal = [0, 22, 25][i % 3]
    req = f"{role} {word} in {city}" + (f" over {sal}k" if sal else "")
    tasks.append({"id": f"T{i:02d}", "request": req, "my_skills": ["python", "sql", "pandas", "git"],
                  "expect": {"location": city.lower(), "job_type": kind, "min_salary": sal * 1000}})
Path(__file__).resolve().parent.parent.joinpath("benchmarks", "tasks.json").write_text(json.dumps(tasks, indent=1))
print(len(tasks), "tasks")

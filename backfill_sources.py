import json, sys
from fetch_jobs import from_remotive, from_arbeitnow, OUT

queries = sys.argv[1:] or ["python", "devops", "data engineer"]
sources_file = OUT / "sources.json"
sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else {}

index = {}
for q in queries:
    for src in (from_remotive, from_arbeitnow):
        try:
            for j in src(q, 100):
                index[(j["title"].strip().lower(), j["company"].strip().lower())] = j["url"]
        except Exception as e:
            print(f"{src.__name__} failed: {e}")

for f in sorted(OUT.glob("[!_]*.txt")):
    if f.name in sources:
        continue
    lines = f.read_text(encoding="utf-8").split("\n")
    key = (lines[0].strip().lower(), lines[1].strip().lower())
    if key in index:
        sources[f.name] = index[key]
        print("matched", f.name)
    else:
        print("no match", f.name)

sources_file.write_text(json.dumps(sources, indent=2), encoding="utf-8")
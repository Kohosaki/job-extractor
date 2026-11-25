import html, json, re, sys, urllib.parse, urllib.request
from pathlib import Path

OUT = Path("data/samples")
UA = {"User-Agent": "job-extractor-learning-project"}

def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def html_to_text(s):
    s = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"\n\s*\n+", "\n\n", s).strip()

def from_remotive(query, limit):
    url = "https://remotive.com/api/remote-jobs?" + urllib.parse.urlencode(
        {"search": query, "limit": limit})
    for j in get_json(url).get("jobs", []):
        yield {
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": j.get("candidate_required_location", ""),
            "salary": j.get("salary", ""),
            "description": j.get("description", ""),
            "url": j.get("url", ""),
        }

def from_arbeitnow(query, limit):
    n = 0
    for j in get_json("https://www.arbeitnow.com/api/job-board-api").get("data", []):
        haystack = (j.get("title", "") + " " + " ".join(j.get("tags", []))).lower()
        if query.lower() not in haystack:
            continue
        yield {
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": j.get("location", ""),
            "salary": "",
            "description": j.get("description", ""),
            "url": j.get("url", ""),
        }
        n += 1
        if n >= limit:
            break

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:50] or "unknown"

def unique_name(company, title):
    """telus-digital.txt, or telus-digital-content-reviewer.txt if taken, then -2, -3..."""
    name = f"{slugify(company)}.txt"
    if not (OUT / name).exists():
        return name
    stem = f"{slugify(company)}-{slugify(title)}"
    name, n = f"{stem}.txt", 2
    while (OUT / name).exists():
        name = f"{stem}-{n}.txt"
        n += 1
    return name

def main(query, limit=10):
    OUT.mkdir(parents=True, exist_ok=True)
    seen_file = OUT / "_seen_urls.txt"
    seen = set(seen_file.read_text().split()) if seen_file.exists() else set()
    sources_file = OUT / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else {}
    nums = [int(f.stem) for f in OUT.glob("[0-9]*.txt") if f.stem.isdigit()]
    next_id = max(nums, default=0) + 1
    saved = 0

    for source in (from_remotive, from_arbeitnow):
        try:
            jobs = list(source(query, limit))
        except Exception as e:
            print(f"{source.__name__} failed: {e}")
            continue
        for job in jobs:
            if job["url"] in seen:
                continue
            text = (f"Company: {job['company']}\n{job['title']}\n{job['company']}\n"
                    f"{job['location']}\n{job['salary']}\n\n"
                    f"{html_to_text(job['description'])}")
            name = f"{next_id:03d}.txt"
            (OUT / name).write_text(text, encoding="utf-8")
            sources[name] = job["url"]
            seen.add(job["url"])
            print(f"saved {name}  {job['company']} ({job['title']})")
            next_id += 1
            saved += 1
    seen_file.write_text("\n".join(seen))
    sources_file.write_text(json.dumps(sources, indent=2), encoding="utf-8")
    print(f"Done: {saved} new postings")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "python",
         int(sys.argv[2]) if len(sys.argv) > 2 else 10)
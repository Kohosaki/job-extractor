import json, sys
from pathlib import Path
from ollama import chat
from pydantic import ValidationError
from schema import JobPosting

MODEL = "qwen3.5:4b"

SYSTEM = (
    "You extract structured data from job postings. "
    "Output only the JSON object. No explanations, no commentary. "
    "Use null for anything not explicitly stated. Never guess.\n"
    "Rules:\n"
    "- Salary: record the numbers exactly as written, plus the currency "
    "and the pay period (hour, day, month, or year). "
    "If only one figure is given, put it in both salary_min and salary_max. "
    "If no pay is stated, use null for all salary fields.\n"
    "- Remote: use 'remote' only if the posting says remote or work from home, "
    "'hybrid' only if it mentions a mix, and 'onsite' only if it requires "
    "being in an office. Otherwise null.\n"
    "- Skills: list the abilities or qualifications the job requires of the "
    "candidate, in lowercase. Do not list devices, accounts, or software "
    "merely needed to do the task unless the posting names them as a required skill.\n"
)

class ExtractionError(Exception):
    pass

def extract(text: str, max_retries: int = 2) -> JobPosting:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text},
    ]
    for _ in range(max_retries + 1):
        resp = chat(
            model=MODEL,
            messages=messages,
            format=JobPosting.model_json_schema(),
            think=False,
            options={"num_predict": 500, "temperature": 0},
        )
        raw = resp.message.content
        try:
            return JobPosting.model_validate_json(raw)
        except ValidationError as e:
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"That failed validation:\n{e}\nReturn corrected JSON only."},
            ]
    raise ExtractionError("Could not get valid output after retries")

if __name__ == "__main__":
    path = Path(sys.argv[1])
    result = extract(path.read_text(encoding="utf-8")).model_dump()

    sources_file = path.parent / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else {}
    result["source_url"] = sources.get(path.name)

    print(json.dumps(result, indent=2))
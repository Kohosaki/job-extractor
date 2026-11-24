import sys
from ollama import chat
from pydantic import ValidationError
from schema import JobPosting

MODEL = "qwen3.5:4b"

SYSTEM = (
    "You extract structured data from job postings. "
    "Output only the JSON object. No explanations, no commentary. "
    "Use null for anything not explicitly stated. Never guess."
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
    text = open(sys.argv[1], encoding="utf-8").read()
    print(extract(text).model_dump_json(indent=2))
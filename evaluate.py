import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from extractor import extract, ExtractionError

LABELS = Path("data/labels.json")


def norm(v):
    """Make values comparable: trim and lowercase text, leave everything else."""
    return v.strip().lower() if isinstance(v, str) else v


def score_field(expected, got):
    """Return a score from 0.0 to 1.0 for one field."""
    # Lists (skills): overlap between the two sets
    if isinstance(expected, list):
        e = {norm(x) for x in expected}
        g = {norm(x) for x in (got or [])}
        if not e and not g:
            return 1.0
        return len(e & g) / len(e | g)
    # Everything else: exact match after normalizing
    return 1.0 if norm(expected) == norm(got) else 0.0


def main():
    if not LABELS.exists():
        sys.exit("Missing data/labels.json. Label some postings first.")

    cases = json.loads(LABELS.read_text(encoding="utf-8"))
    scores = defaultdict(list)
    mistakes = []
    failures = 0
    start = time.time()

    for i, case in enumerate(cases, 1):
        file = case["file"]
        print(f"[{i}/{len(cases)}] {file} ...", flush=True)
        try:
            text = Path(file).read_text(encoding="utf-8")
            result = extract(text).model_dump()
        except ExtractionError:
            failures += 1
            mistakes.append((file, "EXTRACTION FAILED", "", ""))
            continue
        except Exception as e:
            failures += 1
            mistakes.append((file, f"ERROR: {e}", "", ""))
            continue

        for field, expected in case["expected"].items():
            got = result.get(field)
            s = score_field(expected, got)
            scores[field].append(s)
            if s < 1.0:
                mistakes.append((file, field, expected, got))

    elapsed = time.time() - start

    print("\n=== RESULTS ===")
    print(f"Postings evaluated: {len(cases)}")
    print(f"Extraction failures: {failures}/{len(cases)}")
    print(f"Time: {elapsed:.0f}s ({elapsed / max(len(cases), 1):.1f}s per posting)\n")

    print(f"{'field':<18}{'score':>7}   n")
    for field, vals in scores.items():
        print(f"{field:<18}{sum(vals) / len(vals):>7.0%}   {len(vals)}")

    if scores:
        all_vals = [v for vals in scores.values() for v in vals]
        print(f"\nOverall: {sum(all_vals) / len(all_vals):.0%}")

    if mistakes:
        print("\n=== MISTAKES ===")
        for file, field, expected, got in mistakes:
            print(f"{file}  {field}\n    expected: {expected}\n    got:      {got}")


if __name__ == "__main__":
    main()
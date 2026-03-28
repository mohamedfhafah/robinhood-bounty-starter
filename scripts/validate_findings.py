#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = [
    "id",
    "target_host",
    "target_url",
    "vuln_class",
    "summary",
    "evidence",
    "repro_steps",
    "impact_statement",
    "confidence",
    "need_human_review",
]


def validate_obj(obj: dict, path: Path, idx: int) -> list[str]:
    errs: list[str] = []
    for key in REQUIRED:
        if key not in obj:
            errs.append(f"{path}:{idx}: missing field '{key}'")
    if "confidence" in obj and obj["confidence"] not in {"low", "medium", "high"}:
        errs.append(f"{path}:{idx}: invalid confidence '{obj['confidence']}'")
    if "need_human_review" in obj and not isinstance(obj["need_human_review"], bool):
        errs.append(f"{path}:{idx}: need_human_review must be boolean")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate finding JSONL artifacts")
    ap.add_argument("jsonl", help="Path to findings JSONL file")
    args = ap.parse_args()

    p = Path(args.jsonl)
    if not p.exists():
        print(f"ERROR: file not found: {p}")
        return 2

    errors: list[str] = []
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{p}:{i}: invalid json: {e}")
                continue
            if not isinstance(obj, dict):
                errors.append(f"{p}:{i}: expected JSON object")
                continue
            errors.extend(validate_obj(obj, p, i))

    if errors:
        print("VALIDATION_FAILED")
        for e in errors:
            print(e)
        return 1

    print("VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

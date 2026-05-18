#!/usr/bin/env python3
"""Validate repository eval metadata for Agent Skills."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_trigger_queries(skill_dir: Path, errors: list[str]) -> None:
    path = skill_dir / "evals" / "trigger-queries.json"
    require(path.exists(), errors, f"{path}: missing trigger evals")
    if not path.exists():
        return

    data = load_json(path)
    require(isinstance(data, list), errors, f"{path}: expected a JSON array")
    if not isinstance(data, list):
        return

    positives = 0
    negatives = 0
    for index, item in enumerate(data):
        prefix = f"{path}[{index}]"
        require(isinstance(item, dict), errors, f"{prefix}: expected an object")
        if not isinstance(item, dict):
            continue
        query = item.get("query")
        should_trigger = item.get("should_trigger")
        require(isinstance(query, str) and bool(query.strip()), errors, f"{prefix}.query: expected a non-empty string")
        require(isinstance(should_trigger, bool), errors, f"{prefix}.should_trigger: expected a boolean")
        if should_trigger is True:
            positives += 1
        elif should_trigger is False:
            negatives += 1

    require(positives > 0, errors, f"{path}: expected at least one should_trigger=true case")
    require(negatives > 0, errors, f"{path}: expected at least one should_trigger=false case")


def validate_output_evals(skill_dir: Path, errors: list[str]) -> None:
    path = skill_dir / "evals" / "evals.json"
    require(path.exists(), errors, f"{path}: missing output evals")
    if not path.exists():
        return

    data = load_json(path)
    require(isinstance(data, dict), errors, f"{path}: expected a JSON object")
    if not isinstance(data, dict):
        return

    skill_name = data.get("skill_name")
    require(skill_name == skill_dir.name, errors, f"{path}.skill_name: expected {skill_dir.name!r}")

    evals = data.get("evals")
    require(isinstance(evals, list) and len(evals) > 0, errors, f"{path}.evals: expected a non-empty array")
    if not isinstance(evals, list):
        return

    for index, item in enumerate(evals):
        prefix = f"{path}.evals[{index}]"
        require(isinstance(item, dict), errors, f"{prefix}: expected an object")
        if not isinstance(item, dict):
            continue
        require(isinstance(item.get("id"), (str, int)), errors, f"{prefix}.id: expected a string or integer")
        require(isinstance(item.get("prompt"), str) and bool(item["prompt"].strip()), errors, f"{prefix}.prompt: expected a non-empty string")
        require(
            isinstance(item.get("expected_output"), str) and bool(item["expected_output"].strip()),
            errors,
            f"{prefix}.expected_output: expected a non-empty string",
        )
        if "files" in item:
            files = item["files"]
            require(isinstance(files, list) and all(isinstance(file, str) for file in files), errors, f"{prefix}.files: expected an array of strings")


def main() -> int:
    skill_dirs = sorted(path.parent for path in SKILLS_ROOT.rglob("SKILL.md"))
    errors: list[str] = []

    if not skill_dirs:
        errors.append(f"{SKILLS_ROOT}: no skills found")

    for skill_dir in skill_dirs:
        try:
            validate_trigger_queries(skill_dir, errors)
            validate_output_evals(skill_dir, errors)
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Valid eval metadata for {len(skill_dirs)} skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

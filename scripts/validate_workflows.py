#!/usr/bin/env python3
"""Validate every n8n workflow export in this repository.

Checks performed
  1. The file is valid JSON and looks like an n8n workflow
     (has "nodes" and "connections").
  2. No secret-looking strings are present (API keys, bot tokens,
     real-looking email addresses).

Usage:  python scripts/validate_workflows.py
Exit code is 1 if any problem is found, so it can run in CI.
Standard library only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = {
    "OpenWeatherMap-style key (appid=<32 hex>)": re.compile(r"appid=[0-9a-f]{32}", re.I),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "OpenAI-style secret key": re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    "Telegram bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_\-]{35}\b"),
    "Bearer token": re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"),
}
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_PREFIXES = ("your-", "example", "user@", "name@")


def check_file(path: Path) -> list[str]:
    problems = []
    raw = path.read_text(encoding="utf-8")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if not isinstance(data, dict) or "nodes" not in data or "connections" not in data:
        problems.append('does not look like an n8n workflow (missing "nodes"/"connections")')

    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(raw):
            problems.append(f"possible secret: {label}")

    for email in sorted(set(EMAIL.findall(raw))):
        if not email.lower().startswith(ALLOWED_EMAIL_PREFIXES):
            problems.append(f"real-looking email address: {email}")

    return problems


def main() -> int:
    files = sorted((ROOT / "projects").rglob("*.json"))
    if not files:
        print("No workflow files found under projects/")
        return 1

    failed = False
    for path in files:
        problems = check_file(path)
        rel = path.relative_to(ROOT)
        if problems:
            failed = True
            print(f"FAIL  {rel}")
            for p in problems:
                print(f"        - {p}")
        else:
            print(f"OK    {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

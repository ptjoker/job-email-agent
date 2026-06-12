from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APPLICATIONS_DIR = ROOT / "applications"


def safe_slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in cleaned.split("-") if part)[:80] or "job"


def append_application_log(
    job: dict[str, Any],
    cover_letter_path: Path,
    status: str = "drafted",
    note: str = "",
) -> Path:
    APPLICATIONS_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = APPLICATIONS_DIR / f"{today}-applications.md"
    jsonl_path = APPLICATIONS_DIR / f"{today}-applications.jsonl"

    title = job.get("subject") or job.get("title") or "Unknown role"
    company = job.get("company") or job.get("sender") or "Unknown company"
    summary = job.get("snippet") or job.get("description") or "No short description available."
    link = first_link(job)

    if not log_path.exists():
        log_path.write_text(f"# Applications - {today}\n\n", encoding="utf-8")

    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"## {title}\n\n")
        file.write(f"- Status: {status}\n")
        file.write(f"- Company/source: {company}\n")
        file.write(f"- Link: {link or 'Not found'}\n")
        file.write(f"- Cover letter: {cover_letter_path}\n")
        if note:
            file.write(f"- Note: {note}\n")
        file.write(f"- Summary: {summary}\n\n")

    event = {
        "date": today,
        "status": status,
        "title": title,
        "company": company,
        "link": link,
        "cover_letter_path": str(cover_letter_path),
        "summary": summary,
        "note": note,
    }
    with jsonl_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=True) + "\n")

    return log_path


def first_link(job: dict[str, Any]) -> str:
    links = job.get("links") or []
    return str(links[0]) if links else str(job.get("link") or "")


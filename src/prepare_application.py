from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from application_log import APPLICATIONS_DIR, append_application_log, safe_slug
from cover_letter import generate_cover_letter
from cv_reader import read_cv_text


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"
PROFILE_PATH = ROOT / "profile.json"
COVER_LETTERS_DIR = ROOT / "cover_letters"
QUEUE_DIR = ROOT / "applications" / "queue"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def latest_queue_file(require_jobs: bool = True) -> Path:
    files = sorted(QUEUE_DIR.glob("*jobs*.json"), reverse=True)
    if not files:
        raise FileNotFoundError(
            "No job queue found. Run .\\scripts\\dry-run.ps1 or .\\scripts\\run-daily.ps1 first."
        )

    if not require_jobs:
        return files[0]

    for file in files:
        try:
            data = load_json(file)
            if data.get("jobs"):
                return file
        except Exception:
            continue

    raise ValueError(
        "All available job queues are empty. Run a broader dry run, then try prepare-application again."
    )


def load_jobs(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    return list(data.get("jobs", []))


def choose_job(jobs: list[dict[str, Any]], job_index: int) -> dict[str, Any]:
    if job_index < 1 or job_index > len(jobs):
        raise IndexError(f"Job index must be between 1 and {len(jobs)}.")
    return jobs[job_index - 1]


def build_cover_letter_path(job: dict[str, Any]) -> Path:
    COVER_LETTERS_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    title = job.get("subject") or job.get("title") or "job"
    company = job.get("company") or job.get("sender") or "company"
    filename = f"{today}-{safe_slug(company)}-{safe_slug(title)}-cover-letter.md"
    return COVER_LETTERS_DIR / filename


def list_jobs(jobs: list[dict[str, Any]], limit: int) -> None:
    for index, job in enumerate(jobs[:limit], start=1):
        title = job.get("subject") or job.get("title") or "(no title)"
        company = job.get("company") or job.get("sender") or "unknown source"
        score = job.get("score", 0)
        category = job.get("category", "unknown")
        print(f"{index}. [{category} {score}] {title} - {company}")


def run(args: argparse.Namespace) -> None:
    config = load_json(CONFIG_PATH)

    if not PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"Missing {PROFILE_PATH}. Copy profile.example.json to profile.json and edit it."
        )

    profile = load_json(PROFILE_PATH)
    cv_path = args.cv or config.get("application", {}).get("cv_path")
    if not cv_path:
        raise ValueError("Add application.cv_path to config.json or pass --cv.")

    queue_path = Path(args.queue).resolve() if args.queue else latest_queue_file(require_jobs=True)
    jobs = load_jobs(queue_path)
    if not jobs:
        raise ValueError("The selected queue has no jobs.")

    if args.list:
        list_jobs(jobs, args.limit)
        return

    job = choose_job(jobs, args.job_index)
    cv_text = read_cv_text(cv_path)
    letter = generate_cover_letter(job, profile, cv_text)
    letter_path = build_cover_letter_path(job)
    letter_path.write_text(letter, encoding="utf-8")

    log_path = append_application_log(
        job=job,
        cover_letter_path=letter_path,
        status="drafted",
        note=args.note or "Prepared for review. Sensitive fields should be filled manually.",
    )

    APPLICATIONS_DIR.mkdir(exist_ok=True)
    print(f"Created cover letter: {letter_path}")
    print(f"Updated application log: {log_path}")
    links = job.get("links") or []
    if links:
        print(f"Application link: {links[0]}")
    print("Review the cover letter and application page before submitting anything.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a job application draft from the latest ranked jobs."
    )
    parser.add_argument("--job-index", type=int, default=1, help="Ranked job number to prepare.")
    parser.add_argument("--queue", help="Specific queue JSON file to use.")
    parser.add_argument("--cv", help="Path to your CV file.")
    parser.add_argument("--list", action="store_true", help="List ranked jobs and exit.")
    parser.add_argument("--limit", type=int, default=20, help="How many jobs to list.")
    parser.add_argument("--note", default="", help="Optional note to add to the application log.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

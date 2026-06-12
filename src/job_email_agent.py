from __future__ import annotations

import argparse
import base64
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header, make_header
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"
CREDENTIALS_PATH = ROOT / "secrets" / "credentials.json"
TOKEN_PATH = ROOT / "token.json"
DIGEST_DIR = ROOT / "digests"
QUEUE_DIR = ROOT / "applications" / "queue"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


@dataclass
class JobEmail:
    message_id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str
    links: list[str]
    score: int
    category: str
    reasons: list[str]


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Copy config.example.json to config.json and edit it."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_PATH}. Add your Gmail OAuth desktop credentials first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def decode_mime(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def header_value(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return decode_mime(header.get("value", ""))
    return ""


def decode_body(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode(
        "utf-8", errors="ignore"
    )


def collect_text_parts(payload: dict[str, Any]) -> list[str]:
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if body_data and mime_type in {"text/plain", "text/html"}:
        return [strip_html(decode_body(body_data))]

    parts: list[str] = []
    for part in payload.get("parts", []) or []:
        parts.extend(collect_text_parts(part))
    return parts


def collect_raw_parts(payload: dict[str, Any]) -> list[str]:
    body_data = payload.get("body", {}).get("data", "")
    parts = [decode_body(body_data)] if body_data else []
    for part in payload.get("parts", []) or []:
        parts.extend(collect_raw_parts(part))
    return parts


def strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def extract_links(text: str) -> list[str]:
    links = re.findall(r"https?://[^\s<>\"]+", text or "")
    cleaned: list[str] = []
    for link in links:
        link = link.rstrip(").,;]")
        if link not in cleaned:
            cleaned.append(link)
    return cleaned[:10]


def score_message(
    subject: str, sender: str, snippet: str, body: str, config: dict[str, Any]
) -> tuple[int, list[str]]:
    preferences = config["preferences"]
    text = normalize(" ".join([subject, sender, snippet, body]))
    score = 0
    reasons: list[str] = []

    scoring_groups = [
        ("target_titles", 28, "title match"),
        ("preferred_keywords", 10, "preferred keyword"),
        ("locations", 12, "location match"),
        ("seniority", 8, "seniority match"),
    ]

    for key, points, reason_label in scoring_groups:
        matches = [item for item in preferences.get(key, []) if normalize(item) in text]
        if matches:
            score += min(points * len(matches), points * 3)
            reasons.append(f"{reason_label}: {', '.join(matches[:3])}")

    if preferences.get("remote_ok") and re.search(r"\b(remote|work from home|wfh)\b", text):
        score += 12
        reasons.append("remote-friendly")

    avoid_matches = [
        item for item in preferences.get("avoid_keywords", []) if normalize(item) in text
    ]
    if avoid_matches:
        score -= 35
        reasons.append(f"avoid keyword: {', '.join(avoid_matches[:3])}")

    if re.search(r"\b(job alert|jobs you may be interested in|new jobs|hiring)\b", text):
        score += 8
        reasons.append("job alert")

    if re.search(r"\b(expired|no longer accepting|closed)\b", text):
        score -= 30
        reasons.append("possibly expired")

    return max(score, 0), reasons or ["no strong preference match"]


def category_for_score(score: int, config: dict[str, Any]) -> str:
    thresholds = config["thresholds"]
    if score >= thresholds["top"]:
        return "top"
    if score >= thresholds["maybe"]:
        return "maybe"
    return "ignore"


def fetch_message(service, message_id: str, config: dict[str, Any]) -> JobEmail:
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    subject = header_value(headers, "Subject")
    sender = header_value(headers, "From")
    date = header_value(headers, "Date")
    snippet = message.get("snippet", "")
    body = " ".join(collect_text_parts(payload))
    raw_body = " ".join(collect_raw_parts(payload))
    links = extract_links(" ".join([snippet, body, raw_body]))
    score, reasons = score_message(subject, sender, snippet, body, config)
    category = category_for_score(score, config)

    return JobEmail(
        message_id=message_id,
        thread_id=message.get("threadId", ""),
        subject=subject,
        sender=sender,
        date=date,
        snippet=snippet,
        body=body,
        links=links,
        score=score,
        category=category,
        reasons=reasons,
    )


def search_messages(service, query: str, max_messages: int) -> list[str]:
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_messages)
        .execute()
    )
    return [message["id"] for message in response.get("messages", [])]


def ensure_label(service, label_name: str) -> str:
    existing = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in existing:
        if label["name"] == label_name:
            return label["id"]

    created = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    return created["id"]


def apply_labels(service, job_email: JobEmail, label_ids: dict[str, str]) -> None:
    service.users().messages().modify(
        userId="me",
        id=job_email.message_id,
        body={
            "addLabelIds": [
                label_ids[job_email.category],
                label_ids["processed"],
            ]
        },
    ).execute()


def write_digest(job_emails: list[JobEmail], config: dict[str, Any], dry_run: bool) -> Path:
    DIGEST_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    suffix = ".dry-run" if dry_run else ""
    path = DIGEST_DIR / f"{today}-top-jobs{suffix}.md"
    top_limit = config.get("digest_top_limit", 15)
    ranked = sorted(job_emails, key=lambda item: item.score, reverse=True)
    top_jobs = [item for item in ranked if item.category in {"top", "maybe"}][:top_limit]

    lines = [
        f"# Top Jobs Digest - {today}",
        "",
        f"Messages reviewed: {len(job_emails)}",
        f"Top/maybe jobs included: {len(top_jobs)}",
        "",
    ]

    if not top_jobs:
        lines.extend(["No strong matches today.", ""])
    else:
        for index, item in enumerate(top_jobs, start=1):
            lines.extend(
                [
                    f"## {index}. {item.subject or '(no subject)'}",
                    "",
                    f"- Score: {item.score}",
                    f"- Category: {item.category}",
                    f"- From: {item.sender}",
                    f"- Date: {item.date}",
                    f"- Why: {'; '.join(item.reasons)}",
                    f"- Gmail link: https://mail.google.com/mail/u/0/#all/{item.message_id}",
                    "",
                    item.snippet,
                    "",
                ]
            )

    ignored = len([item for item in job_emails if item.category == "ignore"])
    lines.extend(
        [
            "## Cleanup Summary",
            "",
            f"- Top: {len([item for item in job_emails if item.category == 'top'])}",
            f"- Maybe: {len([item for item in job_emails if item.category == 'maybe'])}",
            f"- Ignore-labeled: {ignored}",
            "",
            "No emails were deleted.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    write_job_queue(job_emails, dry_run)
    return path


def write_job_queue(job_emails: list[JobEmail], dry_run: bool) -> Path:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    suffix = ".dry-run" if dry_run else ""
    path = QUEUE_DIR / f"{today}-jobs{suffix}.json"
    ranked = sorted(job_emails, key=lambda item: item.score, reverse=True)
    jobs = [
        {
            "message_id": item.message_id,
            "thread_id": item.thread_id,
            "subject": item.subject,
            "sender": item.sender,
            "date": item.date,
            "snippet": item.snippet,
            "links": item.links,
            "score": item.score,
            "category": item.category,
            "reasons": item.reasons,
        }
        for item in ranked
    ]
    path.write_text(
        json.dumps(
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "dry_run": dry_run,
                "jobs": jobs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def run(dry_run: bool, include_processed: bool = False) -> None:
    config = load_config()
    service = gmail_service()

    query = f"({config['gmail_query']})"
    if not include_processed:
        query = f"{query} -label:{config['labels']['processed']}"
    message_ids = search_messages(service, query, int(config["max_messages"]))
    job_emails = [fetch_message(service, message_id, config) for message_id in message_ids]

    if not dry_run:
        label_ids = {
            key: ensure_label(service, value) for key, value in config["labels"].items()
        }
        for job_email in job_emails:
            apply_labels(service, job_email, label_ids)

    digest_path = write_digest(job_emails, config, dry_run)
    print(f"Reviewed {len(job_emails)} messages.")
    print(f"Wrote digest: {digest_path}")
    if dry_run:
        print("Dry run only: no labels were applied.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage job-alert emails into a daily digest.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create a digest without changing labels in Gmail.",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Include emails already labeled Jobs/Processed. Useful for rebuilding test queues.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    os.chdir(ROOT)
    args = parse_args()
    run(args.dry_run, args.include_processed)

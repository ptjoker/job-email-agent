from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def matched_skills(job_text: str, profile: dict[str, Any], cv_text: str) -> list[str]:
    combined_job = clean_text(job_text).lower()
    combined_cv = clean_text(cv_text).lower()
    skills: list[str] = []

    for skill in profile.get("top_skills", []):
        skill_text = str(skill).strip()
        if not skill_text:
            continue
        normalized = skill_text.lower()
        if normalized in combined_job or normalized in combined_cv:
            skills.append(skill_text)

    return skills[:5]


def generate_cover_letter(
    job: dict[str, Any], profile: dict[str, Any], cv_text: str
) -> str:
    title = clean_text(job.get("subject") or job.get("title") or "the advertised role")
    company = clean_text(job.get("company") or job.get("sender") or "your team")
    description = clean_text(job.get("snippet") or job.get("description") or "")
    skills = matched_skills(" ".join([title, company, description]), profile, cv_text)

    full_name = clean_text(profile.get("full_name", ""))
    current_title = clean_text(profile.get("current_title", ""))
    experience = clean_text(profile.get("experience_summary", ""))
    education = clean_text(profile.get("education_summary", ""))

    skill_sentence = (
        f"My experience with {', '.join(skills[:-1])}, and {skills[-1]} is especially relevant here."
        if len(skills) > 1
        else f"My experience with {skills[0]} is especially relevant here."
        if skills
        else "My background and project experience align with the practical requirements of this role."
    )

    lines = [
        f"{datetime.now().strftime('%d %B %Y')}",
        "",
        "Dear Hiring Team,",
        "",
        f"I am writing to apply for {title}. I was interested in this opportunity because it appears to match the kind of role I am targeting, and I would welcome the chance to contribute to {company}.",
        "",
        f"I am currently positioning myself as {current_title}." if current_title else "",
        f"{experience}" if experience else "",
        f"{education}" if education else "",
        f"{skill_sentence}",
        "",
        "I have attached my CV for your review. I would appreciate the opportunity to discuss how my background, motivation, and ability to learn quickly can support the needs of this role.",
        "",
        "Kind regards,",
        full_name or "[Your name]",
    ]

    return "\n".join(line for line in lines if line != "").strip() + "\n"


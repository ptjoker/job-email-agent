from __future__ import annotations

from pathlib import Path


def read_cv_text(path: str | Path) -> str:
    cv_path = Path(path).expanduser().resolve()
    if not cv_path.exists():
        raise FileNotFoundError(f"CV file not found: {cv_path}")

    suffix = cv_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return cv_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return read_pdf(cv_path)
    if suffix == ".docx":
        return read_docx(cv_path)

    raise ValueError("Supported CV formats: .pdf, .docx, .txt, .md")


def read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def read_docx(path: Path) -> str:
    from docx import Document

    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs).strip()


from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "index.html"


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern), reverse=True)
    return files[0] if files else None


def safe_path(value: str) -> Path:
    path = Path(value).resolve()
    root = ROOT.resolve()
    if root != path and root not in path.parents:
        raise ValueError("File is outside the agent folder.")
    return path


def run_script(script_name: str, *args: str) -> dict:
    command = [sys.executable, str(ROOT / "src" / script_name), *args]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=600,
    )
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def status_payload() -> dict:
    latest_digest = latest_file(ROOT / "digests", "*top-jobs*.md")
    latest_queue = latest_file(ROOT / "applications" / "queue", "*jobs*.json")
    latest_log = latest_file(ROOT / "applications", "*applications.md")

    return {
        "root": str(ROOT),
        "hasConfig": (ROOT / "config.json").exists(),
        "hasProfile": (ROOT / "profile.json").exists(),
        "hasCredentials": (ROOT / "secrets" / "credentials.json").exists(),
        "hasToken": (ROOT / "token.json").exists(),
        "latestDigest": str(latest_digest) if latest_digest else "",
        "latestQueue": str(latest_queue) if latest_queue else "",
        "latestApplicationLog": str(latest_log) if latest_log else "",
    }


def jobs_payload() -> dict:
    queue = latest_file(ROOT / "applications" / "queue", "*jobs*.json")
    if not queue:
        return {"queue": "", "jobs": []}

    data = json.loads(queue.read_text(encoding="utf-8"))
    return {
        "queue": str(queue),
        "createdAt": data.get("created_at", ""),
        "dryRun": data.get("dry_run", False),
        "jobs": data.get("jobs", []),
    }


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text: str, content_type: str = "text/plain") -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path in {"/", "/index.html"}:
            self.send_text(DASHBOARD.read_text(encoding="utf-8"), "text/html")
            return

        if parsed.path == "/api/status":
            self.send_json(status_payload())
            return

        if parsed.path == "/api/jobs":
            self.send_json(jobs_payload())
            return

        if parsed.path == "/api/file":
            query = parse_qs(parsed.query)
            value = query.get("path", [""])[0]
            try:
                path = safe_path(value)
                self.send_json({"path": str(path), "content": path.read_text(encoding="utf-8")})
            except Exception as exc:
                self.send_json({"error": str(exc)}, 400)
            return

        self.send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/dry-run":
            self.send_json(run_script("job_email_agent.py", "--dry-run"))
            return

        if parsed.path == "/api/run-daily":
            self.send_json(run_script("job_email_agent.py"))
            return

        if parsed.path == "/api/prepare":
            payload = self.read_json()
            job_index = str(payload.get("jobIndex", 1))
            self.send_json(run_script("prepare_application.py", "--job-index", job_index))
            return

        self.send_json({"error": "Not found"}, 404)


def main() -> None:
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    url = f"http://{host}:{port}"
    print(f"Job Email Agent dashboard: {url}")
    webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()


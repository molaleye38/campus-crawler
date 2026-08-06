"""Lightweight HTTP server exposing POST /api/cron/crawl-kb for scheduled triggers.

Run with:
    uv run python -m naija_admissions.cron_server

Stdlib-only (no FastAPI/uvicorn dep). Protects with a shared secret via
the CRON_API_KEY env var. When invoked, it triggers a crawl with sensible
scheduled defaults (max=20, all types, resume=True) and writes a crawl_run
record to Supabase keyed by the GitHub Actions run id (or a synthetic id
when invoked outside GH Actions).

Designed for external schedulers (Vercel cron, Railway cron, etc.) that
cannot directly call GitHub Actions workflow_dispatch.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import signal
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .server import _run_scrape

DEFAULT_PORT = 8787
DEFAULT_MAX = 20
DEFAULT_TYPES = ["university", "polytechnic", "college_of_education"]


def _check_api_key(provided: str | None) -> bool:
    expected = os.getenv("CRON_API_KEY")
    if not expected:
        return False
    if not provided:
        return False
    return secrets.compare_digest(provided, expected)


class CronHandler(BaseHTTPRequestHandler):
    def _respond(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._respond(HTTPStatus.OK, {"status": "ok"})
        else:
            self._respond(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/cron/crawl-kb":
            self._respond(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        auth = self.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        if not _check_api_key(token):
            self._respond(HTTPStatus.UNAUTHORIZED, {"error": "invalid or missing api key"})
            return

        body: dict[str, Any] = {}
        length = int(self.headers.get("Content-Length") or 0)
        if length > 0:
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "invalid json body"})
                return

        max_inst = int(body.get("max_institutions", DEFAULT_MAX))
        types = body.get("institution_types") or DEFAULT_TYPES
        failed = body.get("failed_institutions")
        crawl_run_id = body.get("crawl_run_id")
        concurrency = int(body.get("concurrency", 2))
        dry_run = bool(body.get("dry_run", False))

        try:
            result = asyncio.run(_run_scrape(
                max_institutions=max_inst,
                institution_types=types,
                resume_run=True,
                sample_by_type=True,
                force_overwrite=False,
                failed_institutions=failed,
                crawl_run_id=crawl_run_id,
                concurrency=concurrency,
                dry_run=dry_run,
            ))
            self._respond(HTTPStatus.OK, {"status": "ok", "result": result})
        except Exception as e:
            self._respond(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"[cron_server] {self.address_string()} - {format % args}\n")


def main() -> int:
    if not os.getenv("CRON_API_KEY"):
        print("ERROR: CRON_API_KEY env var must be set to start the cron server.", file=sys.stderr)
        return 1
    port = int(os.getenv("CRON_PORT", str(DEFAULT_PORT)))
    host = os.getenv("CRON_HOST", "0.0.0.0")

    server = ThreadingHTTPServer((host, port), CronHandler)

    def shutdown(signum: int, frame: Any) -> None:
        server.shutdown()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"[cron_server] listening on {host}:{port}", file=sys.stderr)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

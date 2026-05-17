"""Fixtures for deterministic demo automation scenarios."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator
from urllib.parse import parse_qs, urlparse

import pytest


class _DemoAutomationHandler(BaseHTTPRequestHandler):
    """Minimal HTTP app used by the built-in demo automation suite."""

    server_version = "DemoAutomationHTTP/1.0"
    valid_username = "tester"
    valid_password = "Passw0rd!"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _read_body(self) -> bytes:
        content_length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(content_length)

    def _write_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/login":
            self._write_html(
                200,
                """
                <html>
                  <head><title>Demo Login</title></head>
                  <body>
                    <h1>Login</h1>
                    <form id="login-form" method="post" action="/login">
                      <input name="username" />
                      <input name="password" type="password" />
                      <button type="submit">Sign in</button>
                    </form>
                  </body>
                </html>
                """.strip(),
            )
            return

        if path == "/dashboard":
            self._write_html(
                200,
                """
                <html>
                  <head><title>Dashboard</title></head>
                  <body>
                    <h1>Welcome Test User</h1>
                    <p>Smoke dashboard ready.</p>
                  </body>
                </html>
                """.strip(),
            )
            return

        self._write_json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/login":
            payload = json.loads(self._read_body().decode("utf-8") or "{}")
            if (
                payload.get("username") == self.valid_username
                and payload.get("password") == self.valid_password
            ):
                self._write_json(200, {"token": "demo-token", "user": self.valid_username})
                return
            self._write_json(401, {"error": "invalid_credentials"})
            return

        if path == "/api/upload":
            filename = self.headers.get("X-Filename", "").strip()
            content = self._read_body()
            if not filename:
                self._write_json(400, {"error": "missing_filename"})
                return
            if not content:
                self._write_json(400, {"error": "empty_file"})
                return
            self._write_json(
                201,
                {
                    "filename": filename,
                    "size": len(content),
                    "content_type": self.headers.get("Content-Type", "application/octet-stream"),
                },
            )
            return

        if path == "/login":
            form_data = parse_qs(self._read_body().decode("utf-8"))
            username = form_data.get("username", [""])[0]
            password = form_data.get("password", [""])[0]
            if username == self.valid_username and password == self.valid_password:
                self._write_html(
                    200,
                    """
                    <html>
                      <head><title>Dashboard</title></head>
                      <body>
                        <h1>Welcome Test User</h1>
                        <p>Login flow succeeded.</p>
                      </body>
                    </html>
                    """.strip(),
                )
                return
            self._write_html(401, "<html><body><h1>Login Failed</h1></body></html>")
            return

        self._write_json(404, {"error": "not_found", "path": path})


@pytest.fixture(scope="session")
def demo_base_url() -> Iterator[str]:
    """Serve a deterministic local app used by automation scenario tests."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DemoAutomationHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

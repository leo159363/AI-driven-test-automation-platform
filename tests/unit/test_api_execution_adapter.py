"""Unit tests for the API execution adapter."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from typing import Generator

import pytest

from src.observability.dashboard.services.api_execution_adapter import (
    DRY_RUN,
    FAILED,
    PASSED,
    ApiExecutionAdapter,
)
from src.observability.dashboard.services.execution_plan_service import build_execution_plan


class _DemoAPIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        if self.path == "/api/login":
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            if payload == {"username": "tester", "password": "Passw0rd!"}:
                self._send_json(200, {"token": "demo-token", "user": "tester"})
            else:
                self._send_json(401, {"error": "invalid_credentials"})
            return

        if self.path == "/api/upload":
            filename = self.headers.get("X-Filename", "")
            if filename and raw_body:
                self._send_json(201, {"filename": filename, "size": len(raw_body)})
            else:
                self._send_json(400, {"error": "invalid_upload"})
            return

        self._send_json(404, {"error": "not_found"})

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture()
def demo_api_base_url() -> Generator[str, None, None]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DemoAPIHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class TestApiExecutionAdapter:
    """Verify deterministic API execution behavior."""

    def test_executes_api_login_plan(self, demo_api_base_url: str) -> None:
        plan = build_execution_plan(
            "API Login",
            "\n".join(
                [
                    "POST /api/login",
                    "等待 响应返回",
                    "断言看到 token",
                ]
            ),
        )

        result = ApiExecutionAdapter(demo_api_base_url).run(plan)

        assert result.status == PASSED
        assert result.passed_steps == 3
        assert result.failed_steps == 0
        assert result.failure_reason is None
        assert result.step_results[0].response_status == 200

    def test_executes_api_upload_plan_with_prepared_file(self, demo_api_base_url: str) -> None:
        plan = build_execution_plan(
            "API Upload",
            "\n".join(
                [
                    "上传 demo.txt",
                    "POST /api/upload",
                    "断言看到 filename",
                ]
            ),
        )

        result = ApiExecutionAdapter(demo_api_base_url).run(plan)

        assert result.status == PASSED
        assert result.passed_steps == 3
        assert result.step_results[1].response_status == 201
        assert "demo.txt" in result.step_results[1].response_preview

    def test_dry_run_does_not_send_network_request(self) -> None:
        plan = build_execution_plan("Dry Run", "POST /api/login\n断言看到 token")

        result = ApiExecutionAdapter("http://127.0.0.1:1").run(plan, dry_run=True)

        assert result.status == DRY_RUN
        assert result.dry_run_steps == 2
        assert result.failed_steps == 0
        assert result.step_results[0].request_url == "http://127.0.0.1:1/api/login"

    def test_fails_when_assertion_text_is_missing(self, demo_api_base_url: str) -> None:
        plan = build_execution_plan("Missing Assertion", "POST /api/login\n断言看到 missing-token")

        result = ApiExecutionAdapter(demo_api_base_url).run(plan)

        assert result.status == FAILED
        assert result.failed_steps == 1
        assert result.failure_reason == "Response does not contain expected text: missing-token"

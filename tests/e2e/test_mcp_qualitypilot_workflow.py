"""End-to-end MCP tools/call workflow for QualityPilot.

This test drives the real MCP stdio server as a JSON-RPC client. It validates
that the QualityPilot testing workflow works at the MCP protocol layer, not only
through direct Python function calls.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Optional

import pytest

from scripts.run_qualitypilot_demo import DEFAULT_REQUIREMENT, DEMO_CONTEXTS, DEMO_STEPS
from scripts.run_qualitypilot_demo import _start_demo_server


PROJECT_ROOT = Path(__file__).parent.parent.parent


class MCPStdioClient:
    """Small JSON-RPC client for the MCP stdio subprocess."""

    def __init__(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "src.mcp_server.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        self._next_id = 1
        self._responses: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._pending: Dict[int, Dict[str, Any]] = {}
        self._stop_reader = threading.Event()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def initialize(self) -> Dict[str, Any]:
        response = self.request(
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "clientInfo": {"name": "qualitypilot-workflow-e2e", "version": "1.0.0"},
                "capabilities": {},
            },
            timeout=30.0,
        )
        self.notification("notifications/initialized")
        return response

    def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        response = self.request(
            method="tools/call",
            params={"name": name, "arguments": arguments},
            timeout=timeout,
        )
        assert "result" in response, response
        result = response["result"]
        assert result.get("isError") is not True, result
        content = result.get("content", [])
        assert content and content[0].get("type") == "text", result
        return json.loads(content[0]["text"])

    def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
        )
        return self._wait_response(request_id, timeout=timeout)

    def notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def close(self) -> None:
        self._stop_reader.set()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)

    def _send(self, message: Dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _read_stdout(self) -> None:
        assert self.proc.stdout is not None
        while not self._stop_reader.is_set():
            line = self.proc.stdout.readline()
            if not line:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if "id" in payload and ("result" in payload or "error" in payload):
                self._responses.put(payload)

    def _wait_response(self, request_id: int, timeout: float) -> Dict[str, Any]:
        if request_id in self._pending:
            return self._pending.pop(request_id)

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                response = self._responses.get(timeout=0.2)
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise AssertionError(f"MCP server exited with code {self.proc.returncode}")
                continue

            response_id = response.get("id")
            if response_id == request_id:
                return response
            if isinstance(response_id, int):
                self._pending[response_id] = response

        stderr = ""
        if self.proc.stderr is not None and self.proc.poll() is not None:
            stderr = self.proc.stderr.read()
        raise AssertionError(f"Timed out waiting for response id={request_id}. stderr={stderr}")


@pytest.mark.e2e
def test_qualitypilot_mcp_tools_call_workflow(tmp_path: Path) -> None:
    """Run the full QualityPilot workflow through MCP tools/call."""
    api_server, api_thread, base_url = _start_demo_server()
    client = MCPStdioClient()
    try:
        init_response = client.initialize()
        assert init_response["result"]["serverInfo"]["name"] == "qualitypilot"

        test_cases = client.call_tool(
            "generate_test_cases",
            {
                "requirement": DEFAULT_REQUIREMENT,
                "project": "qualitypilot-demo",
                "module": "auth",
                "version": "v1",
                "dimensions": ["functional", "negative", "security", "regression"],
                "case_count": 4,
                "contexts": DEMO_CONTEXTS,
            },
        )
        assert test_cases["generation_strategy"] == "rule_based_with_rag_context"
        assert len(test_cases["test_cases"]) == 4
        assert test_cases["test_cases"][0]["citations"][0]["source_id"] == "auth-api-v1"

        junit_path = tmp_path / "junit.xml"
        allure_dir = tmp_path / "allure-results"
        execution = client.call_tool(
            "run_api_tests",
            {
                "scenario_id": "api_login",
                "base_url": base_url,
                "dry_run": False,
                "execution_mode": "plan",
                "step_text": DEMO_STEPS,
                "junitxml": str(junit_path),
                "allure_results": str(allure_dir),
                "record_history": False,
            },
        )
        assert execution["status"] == "failed"
        assert execution["summary"]["failed"] == 1
        assert Path(execution["report_paths"]["junitxml"]).exists()

        report = client.call_tool(
            "get_test_report",
            {
                "run_id": execution["run_id"],
                "report_path": execution["report_paths"]["junitxml"],
                "allure_results": execution["report_paths"]["allure_results"],
            },
        )
        assert report["status"] == "failed"
        assert report["summary"]["failed"] == 1

        failed_cases = client.call_tool(
            "query_failed_cases",
            {
                "run_id": execution["run_id"],
                "report_path": execution["report_paths"]["junitxml"],
                "statuses": ["failure", "error"],
                "keyword": "token",
                "limit": 5,
                "include_details": True,
            },
        )
        assert failed_cases["status"] == "cases_found"
        assert failed_cases["case_count"] == 1
        assert failed_cases["cases"][0]["status"] == "failure"

        failure_analysis = client.call_tool(
            "analyze_failure",
            {
                "run_id": execution["run_id"],
                "report_path": execution["report_paths"]["junitxml"],
                "failed_cases": failed_cases["cases"],
                "contexts": DEMO_CONTEXTS,
                "project": "qualitypilot-demo",
                "module": "auth",
                "version": "v1",
            },
        )
        assert failure_analysis["status"] == "analyzed"
        assert failure_analysis["case_count"] == 1
        assert failure_analysis["analyses"][0]["should_create_bug"] is True

        bug_report = client.call_tool(
            "generate_bug_report",
            {
                "run_id": execution["run_id"],
                "report_path": execution["report_paths"]["junitxml"],
                "analyses": failure_analysis["analyses"],
                "project": "qualitypilot-demo",
                "module": "auth",
                "version": "v1",
                "environment": "e2e",
                "reporter": "QualityPilot",
            },
        )
        assert bug_report["status"] == "generated"
        assert bug_report["bug_count"] == 1
        assert bug_report["bug_reports"][0]["source"]["case_id"] == "FC-001"
        assert "token" in bug_report["markdown"]
    finally:
        client.close()
        api_server.shutdown()
        api_server.server_close()
        api_thread.join(timeout=5)

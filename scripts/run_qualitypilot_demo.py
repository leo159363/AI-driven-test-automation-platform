"""Run a deterministic QualityPilot end-to-end interview demo.

The demo starts a tiny local HTTP service, executes an API scenario that fails
because the response does not contain a token, then runs the MCP workflow:

test case generation -> API execution -> report parsing -> failed-case query
-> failure analysis -> bug report generation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Any, Dict, List, Tuple

from src.mcp_server.tools.analyze_failure import analyze_failure_payload
from src.mcp_server.tools.generate_bug_report import generate_bug_report_payload
from src.mcp_server.tools.generate_test_cases import generate_test_cases_payload
from src.mcp_server.tools.get_test_report import get_test_report_payload
from src.mcp_server.tools.query_failed_cases import query_failed_cases_payload
from src.mcp_server.tools.run_api_tests import run_api_tests_payload


DEFAULT_REQUIREMENT = (
    "The login API should authenticate username and password, return HTTP 200 "
    "with a token field after successful login, and provide clear error messages "
    "without leaking whether the account exists."
)

DEMO_CONTEXTS: List[Dict[str, Any]] = [
    {
        "chunk_id": "auth-api-v1_0001",
        "source_id": "auth-api-v1",
        "source_type": "api_doc",
        "title": "Login API contract",
        "content": "POST /api/login returns HTTP 200 and a token field after successful authentication.",
        "score": 0.96,
        "metadata": {
            "project": "qualitypilot-demo",
            "module": "auth",
            "version": "v1",
            "source_type": "api_doc",
            "source_id": "auth-api-v1",
        },
    },
    {
        "chunk_id": "auth-requirement-v1_0001",
        "source_id": "auth-requirement-v1",
        "source_type": "requirement",
        "title": "Login requirement",
        "content": "Successful login must issue a token. Failed login must not reveal whether the account exists.",
        "score": 0.92,
        "metadata": {
            "project": "qualitypilot-demo",
            "module": "auth",
            "version": "v1",
            "source_type": "requirement",
            "source_id": "auth-requirement-v1",
        },
    },
]

DEMO_STEPS = "\n".join(
    [
        "POST /api/login",
        "wait response returned",
        "assert text token",
    ]
)


class _DemoLoginHandler(BaseHTTPRequestHandler):
    """Local stub API for the interview demo."""

    def do_POST(self) -> None:
        if self.path != "/api/login":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length:
            self.rfile.read(content_length)

        payload = {
            "code": 0,
            "message": "login success",
            "user": "tester",
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _start_demo_server() -> Tuple[ThreadingHTTPServer, threading.Thread, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DemoLoginHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


async def run_demo(
    output_dir: str | Path = "reports/qualitypilot-demo",
    requirement: str = DEFAULT_REQUIREMENT,
) -> Dict[str, Any]:
    """Run the full deterministic demo and return a structured summary."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    server, thread, base_url = _start_demo_server()
    try:
        test_cases = await generate_test_cases_payload(
            requirement=requirement,
            project="qualitypilot-demo",
            module="auth",
            version="v1",
            dimensions=["functional", "negative", "security", "regression"],
            case_count=4,
            top_k=3,
            contexts=DEMO_CONTEXTS,
        )

        execution = run_api_tests_payload(
            scenario_id="api_login",
            base_url=base_url,
            dry_run=False,
            execution_mode="plan",
            step_text=DEMO_STEPS,
            junitxml=str(output_path / "junit.xml"),
            allure_results=str(output_path / "allure-results"),
            record_history=False,
        )

        report = get_test_report_payload(
            run_id=execution["run_id"],
            report_path=execution["report_paths"]["junitxml"],
            project_root=".",
            allure_results=execution["report_paths"].get("allure_results"),
            include_failed_cases=True,
        )

        failed_cases = query_failed_cases_payload(
            run_id=execution["run_id"],
            report_path=execution["report_paths"]["junitxml"],
            project_root=".",
            statuses=["failure", "error"],
            keyword="token",
            limit=10,
            include_details=True,
        )

        failure_analysis = analyze_failure_payload(
            run_id=execution["run_id"],
            report_path=execution["report_paths"]["junitxml"],
            project_root=".",
            failed_cases=failed_cases["cases"],
            contexts=DEMO_CONTEXTS,
            project="qualitypilot-demo",
            module="auth",
            version="v1",
            analysis_depth="standard",
        )

        bug_report = generate_bug_report_payload(
            run_id=execution["run_id"],
            report_path=execution["report_paths"]["junitxml"],
            analyses=failure_analysis["analyses"],
            project="qualitypilot-demo",
            module="auth",
            version="v1",
            environment="local-demo",
            reporter="QualityPilot",
            include_markdown=True,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    summary = {
        "workflow": [
            "generate_test_cases",
            "run_api_tests",
            "get_test_report",
            "query_failed_cases",
            "analyze_failure",
            "generate_bug_report",
        ],
        "requirement": requirement,
        "base_url": base_url,
        "run_id": execution["run_id"],
        "outputs": {
            "output_dir": str(output_path),
            "junitxml": execution["report_paths"]["junitxml"],
            "allure_results": execution["report_paths"].get("allure_results", ""),
            "summary_json": str(output_path / "demo_summary.json"),
            "bug_report_md": str(output_path / "bug_report.md"),
        },
        "stages": {
            "rag_contexts": {
                "strategy": "fixture_contexts_for_stable_interview_demo",
                "contexts": DEMO_CONTEXTS,
            },
            "test_cases": test_cases,
            "execution": execution,
            "report": report,
            "failed_cases": failed_cases,
            "failure_analysis": failure_analysis,
            "bug_report": bug_report,
        },
        "headline": {
            "execution_status": execution["status"],
            "report_status": report["status"],
            "failed_case_count": failed_cases["case_count"],
            "analysis_count": failure_analysis["case_count"],
            "bug_count": bug_report["bug_count"],
        },
    }

    (output_path / "demo_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_path / "bug_report.md").write_text(
        bug_report.get("markdown", ""),
        encoding="utf-8",
    )
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the QualityPilot end-to-end demo.")
    parser.add_argument(
        "--output-dir",
        default="reports/qualitypilot-demo",
        help="Directory for JUnit, Allure results, JSON summary, and bug report markdown.",
    )
    parser.add_argument(
        "--requirement",
        default=DEFAULT_REQUIREMENT,
        help="Requirement text used for test case generation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON summary instead of a short console summary.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    summary = asyncio.run(run_demo(output_dir=args.output_dir, requirement=args.requirement))

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    headline = summary["headline"]
    outputs = summary["outputs"]
    print("QualityPilot demo completed")
    print(f"run_id={summary['run_id']}")
    print(f"execution_status={headline['execution_status']}")
    print(f"report_status={headline['report_status']}")
    print(f"failed_case_count={headline['failed_case_count']}")
    print(f"bug_count={headline['bug_count']}")
    print(f"junitxml={outputs['junitxml']}")
    print(f"allure_results={outputs['allure_results']}")
    print(f"summary_json={outputs['summary_json']}")
    print(f"bug_report_md={outputs['bug_report_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

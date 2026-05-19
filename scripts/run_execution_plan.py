#!/usr/bin/env python
r"""Run a natural-language execution plan through API or browser adapters.

Examples:
    .\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario api_login --dry-run
    .\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario api_login --base-url http://127.0.0.1:8000
    .\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario ui_login_smoke --adapter browser --dry-run
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.observability.dashboard.services import (  # noqa: E402
    DEFAULT_EXECUTION_PLAN_ALLURE_RESULTS_DIR,
    DEFAULT_EXECUTION_PLAN_JUNIT_PATH,
    build_execution_plan,
    execute_plan_with_browser_adapter,
    execute_plan_with_api_adapter,
    get_execution_preset_steps,
    list_automation_scenarios,
    write_execution_result_allure_results,
    write_execution_result_junit_xml,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    scenario_ids = [scenario.scenario_id for scenario in list_automation_scenarios()]
    parser = argparse.ArgumentParser(description="Run an execution plan with an execution adapter.")
    parser.add_argument(
        "--scenario",
        default="api_login",
        choices=scenario_ids,
        help="Built-in scenario id used as the natural-language step source.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL for real API or browser execution.",
    )
    parser.add_argument(
        "--adapter",
        choices=("auto", "api", "browser"),
        default="auto",
        help="Adapter to use. Auto chooses from the parsed execution plan.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview execution without sending network requests.",
    )
    parser.add_argument(
        "--junitxml",
        default=str(DEFAULT_EXECUTION_PLAN_JUNIT_PATH),
        help="JUnit XML output path.",
    )
    parser.add_argument(
        "--allure-results",
        default="",
        help=(
            "Optional Allure results directory. Example: "
            f"{DEFAULT_EXECUTION_PLAN_ALLURE_RESULTS_DIR}"
        ),
    )
    parser.add_argument(
        "--screenshot-dir",
        default="reports/screenshots",
        help="Directory for browser failure screenshots.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full execution result JSON.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the selected execution plan and write a JUnit report."""
    args = parse_args()
    step_text = get_execution_preset_steps(args.scenario)
    if not step_text:
        print(f"No execution preset found for scenario: {args.scenario}", file=sys.stderr)
        return 2

    plan = build_execution_plan(args.scenario, step_text)
    adapter_name = _resolve_adapter(getattr(args, "adapter", "auto"), plan.adapter)
    if adapter_name == "api":
        result = execute_plan_with_api_adapter(
            plan,
            base_url=args.base_url,
            dry_run=args.dry_run,
        )
    elif adapter_name == "browser":
        result = execute_plan_with_browser_adapter(
            plan,
            base_url=args.base_url,
            dry_run=args.dry_run,
            screenshot_dir=getattr(args, "screenshot_dir", "reports/screenshots"),
        )
    else:
        print(f"No executable adapter for plan adapter: {plan.adapter}", file=sys.stderr)
        return 2

    report_path = write_execution_result_junit_xml(result, args.junitxml)
    allure_results = getattr(args, "allure_results", "")
    allure_path = None
    if allure_results:
        allure_path = write_execution_result_allure_results(result, allure_results)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"scenario={args.scenario}")
        print(f"adapter={result.adapter}")
        print(f"status={result.status}")
        print(f"steps={result.total_steps}")
        print(f"passed={result.passed_steps}")
        print(f"failed={result.failed_steps}")
        print(f"skipped={result.skipped_steps}")
        print(f"dry_run={result.dry_run_steps}")
        print(f"junitxml={report_path}")
        if allure_path:
            print(f"allure_result={allure_path}")
        if result.failure_reason:
            print(f"failure_reason={result.failure_reason}")

    return 1 if result.failed_steps else 0


def _resolve_adapter(requested_adapter: str, plan_adapter: str) -> str:
    if requested_adapter == "api":
        return "api"
    if requested_adapter == "browser":
        return "browser"
    if plan_adapter == "api_http_preview":
        return "api"
    if plan_adapter == "ui_browser_preview":
        return "browser"
    return ""


def _configure_console_encoding() -> None:
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


if __name__ == "__main__":
    _configure_console_encoding()
    raise SystemExit(main())

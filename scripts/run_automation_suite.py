"""Run the platform's built-in demo automation scenarios with report outputs.

Usage:
    .\.venv\Scripts\python.exe scripts\run_automation_suite.py --scenario all
    .\.venv\Scripts\python.exe scripts\run_automation_suite.py --scenario api_login
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Sequence

import pytest

from src.observability.dashboard.services.automation_scenario_service import (
    get_pytest_targets,
    list_automation_scenarios,
)


def _parser() -> argparse.ArgumentParser:
    scenario_choices = ["all"] + [scenario.scenario_id for scenario in list_automation_scenarios()]
    parser = argparse.ArgumentParser(description="Run built-in demo automation scenarios.")
    parser.add_argument(
        "--scenario",
        default="all",
        choices=scenario_choices,
        help="Scenario id to run, or 'all' to run every built-in demo scenario.",
    )
    parser.add_argument(
        "--junitxml",
        default="reports/junit.xml",
        help="Path to the output JUnit XML file.",
    )
    parser.add_argument(
        "--allure-results",
        default="reports/allure-results",
        help="Directory for Allure results when allure-pytest is installed.",
    )
    parser.add_argument(
        "--disable-allure",
        action="store_true",
        help="Skip Allure output even if allure-pytest is available.",
    )
    return parser


def _allure_available() -> bool:
    return importlib.util.find_spec("allure_pytest") is not None


def build_pytest_args(
    scenario_id: str,
    junitxml_path: str,
    allure_results_path: str,
    use_allure: bool,
) -> list[str]:
    """Build pytest CLI args for the selected automation suite."""
    junit_path = Path(junitxml_path)
    junit_path.parent.mkdir(parents=True, exist_ok=True)

    args = list(get_pytest_targets(scenario_id))
    args.extend(
        [
            "-m",
            "automation",
            f"--junitxml={junit_path}",
            "-v",
        ]
    )

    if use_allure:
        allure_path = Path(allure_results_path)
        allure_path.mkdir(parents=True, exist_ok=True)
        args.append(f"--alluredir={allure_path}")

    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    use_allure = _allure_available() and not args.disable_allure

    pytest_args = build_pytest_args(
        scenario_id=args.scenario,
        junitxml_path=args.junitxml,
        allure_results_path=args.allure_results,
        use_allure=use_allure,
    )

    print(f"[automation-runner] scenario={args.scenario}")
    print(f"[automation-runner] junitxml={args.junitxml}")
    if use_allure:
        print(f"[automation-runner] alluredir={args.allure_results}")
    else:
        print("[automation-runner] allure-pytest not available; skipping Allure output")
    print(f"[automation-runner] pytest args: {' '.join(pytest_args)}")

    return pytest.main(pytest_args)


if __name__ == "__main__":
    raise SystemExit(main())

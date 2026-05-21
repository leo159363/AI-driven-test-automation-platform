"""Tests for the dashboard test-case catalog service."""

from src.observability.dashboard.services.test_case_library_service import (
    build_api_request_rows,
    build_case_catalog_rows,
    build_scenario_execution_command,
    list_test_cases,
    summarize_test_cases,
)


def test_list_test_cases_contains_api_and_ui_cases() -> None:
    cases = list_test_cases()

    assert len(cases) >= 6
    assert any(case.test_type == "接口测试" for case in cases)
    assert any(case.test_type == "界面测试" for case in cases)
    assert any(case.scenario_id == "api_login" for case in cases)


def test_build_case_catalog_rows_is_dashboard_friendly() -> None:
    rows = build_case_catalog_rows()

    assert rows
    assert {"用例ID", "标题", "类型", "模块", "自动化状态", "pytest目标"}.issubset(rows[0])


def test_build_api_request_rows_links_cases() -> None:
    rows = build_api_request_rows()

    assert rows
    assert rows[0]["方法"] == "POST"
    assert rows[0]["关联用例"].startswith("TC-API-")
    assert rows[0]["自动化状态"] == "已自动化"


def test_api_request_examples_are_frontend_ready() -> None:
    from src.observability.dashboard.services.test_case_library_service import (
        list_api_request_examples,
    )

    examples = list_api_request_examples()

    assert examples
    assert all(example.endpoint_id for example in examples)
    assert all(example.module for example in examples)
    assert all(example.headers for example in examples)
    assert all(example.assertions for example in examples)
    assert all(example.scenario_id for example in examples)
    assert any(example.path == "/api/upload" for example in examples)


def test_summarize_test_cases_counts_core_dimensions() -> None:
    summary = summarize_test_cases()

    assert summary["total"] >= 6
    assert summary["api"] >= 4
    assert summary["ui"] >= 2
    assert summary["automated"] >= 4


def test_build_scenario_execution_command_includes_reports() -> None:
    command = build_scenario_execution_command("api_login")

    assert "run_automation_suite.py --scenario api_login" in command
    assert "reports/dashboard-api_login-junit.xml" in command
    assert "reports/dashboard-api_login-allure-results" in command

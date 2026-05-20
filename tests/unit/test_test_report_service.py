"""Unit tests for test report discovery and JUnit parsing."""

from __future__ import annotations

from pathlib import Path

from src.observability.dashboard.services.test_report_service import (
    discover_report_artifacts,
    get_default_junit_report_path,
    load_execution_summary,
    parse_junit_xml,
)


class TestTestReportService:
    """Verify report discovery and JUnit XML parsing."""

    def test_parse_single_testsuite_report(self, tmp_path: Path) -> None:
        report = tmp_path / "junit.xml"
        report.write_text(
            """
<testsuite name="pytest" tests="5" failures="1" errors="0" skipped="1" time="3.25">
  <testcase classname="api" name="test_ok" />
</testsuite>
            """.strip(),
            encoding="utf-8",
        )

        summary = parse_junit_xml(report)

        assert summary.suite_name == "pytest"
        assert summary.total == 5
        assert summary.passed == 3
        assert summary.failed == 1
        assert summary.skipped == 1
        assert summary.errors == 0
        assert summary.duration_seconds == 3.25

    def test_parse_testsuites_report(self, tmp_path: Path) -> None:
        report = tmp_path / "junit.xml"
        report.write_text(
            """
<testsuites name="full-run">
  <testsuite name="suite-a" tests="2" failures="1" errors="0" skipped="0" time="1.5" />
  <testsuite name="suite-b" tests="3" failures="0" errors="1" skipped="1" time="2.0" />
</testsuites>
            """.strip(),
            encoding="utf-8",
        )

        summary = parse_junit_xml(report)

        assert summary.suite_name == "full-run"
        assert summary.total == 5
        assert summary.passed == 2
        assert summary.failed == 1
        assert summary.errors == 1
        assert summary.skipped == 1
        assert summary.duration_seconds == 3.5

    def test_discover_report_artifacts_detects_junit_and_allure(self, tmp_path: Path) -> None:
        junit_report = tmp_path / "reports" / "junit.xml"
        junit_report.parent.mkdir(parents=True)
        junit_report.write_text("<testsuite tests='1' />", encoding="utf-8")

        execution_plan_allure = tmp_path / "reports" / "execution-plan-allure-results"
        execution_plan_allure.mkdir(parents=True)
        (execution_plan_allure / "plan-result.json").write_text("{}", encoding="utf-8")

        qualitypilot_allure = tmp_path / "reports" / "qualitypilot-demo" / "allure-results"
        qualitypilot_allure.mkdir(parents=True)
        (qualitypilot_allure / "demo-result.json").write_text("{}", encoding="utf-8")

        allure_results = tmp_path / "reports" / "allure-results"
        allure_results.mkdir(parents=True)
        (allure_results / "case-1-result.json").write_text("{}", encoding="utf-8")
        (allure_results / "case-2-result.json").write_text("{}", encoding="utf-8")

        qualitypilot_report = tmp_path / "reports" / "qualitypilot-demo" / "allure-report"
        qualitypilot_report.mkdir(parents=True)
        (qualitypilot_report / "index.html").write_text("<html></html>", encoding="utf-8")

        allure_report = tmp_path / "reports" / "allure-report"
        allure_report.mkdir(parents=True)
        (allure_report / "index.html").write_text("<html></html>", encoding="utf-8")

        artifacts = discover_report_artifacts(tmp_path)

        assert any(
            artifact.artifact_type == "junit_xml"
            and artifact.exists
            and artifact.path == junit_report
            for artifact in artifacts
        )
        assert any(
            artifact.artifact_type == "allure_results"
            and artifact.exists
            and artifact.path == qualitypilot_allure
            and artifact.detail == "1 result files"
            for artifact in artifacts
        )
        assert any(
            artifact.artifact_type == "allure_results"
            and artifact.exists
            and artifact.path == execution_plan_allure
            and artifact.detail == "1 result files"
            for artifact in artifacts
        )
        assert any(
            artifact.artifact_type == "allure_results"
            and artifact.exists
            and artifact.path == allure_results
            and artifact.detail == "2 result files"
            for artifact in artifacts
        )
        assert any(
            artifact.artifact_type == "allure_report"
            and artifact.exists
            and artifact.path == qualitypilot_report
            and artifact.detail == "Static HTML report ready"
            for artifact in artifacts
        )
        assert any(
            artifact.artifact_type == "allure_report"
            and artifact.exists
            and artifact.detail == "Static HTML report ready"
            for artifact in artifacts
        )

    def test_default_junit_report_path_prefers_existing_report(self, tmp_path: Path) -> None:
        junit_report = tmp_path / "reports" / "junit.xml"
        junit_report.parent.mkdir(parents=True)
        junit_report.write_text("<testsuite tests='1' />", encoding="utf-8")

        assert get_default_junit_report_path(tmp_path) == str(junit_report)

    def test_load_execution_summary_returns_warning_for_missing_report(self) -> None:
        summary, warning = load_execution_summary("reports/not-found.xml")

        assert summary is None
        assert warning == "当前未找到 JUnit XML 报告。请先运行 pytest 并生成报告。"

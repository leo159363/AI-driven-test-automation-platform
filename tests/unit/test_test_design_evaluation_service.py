"""Unit tests for deterministic test-design evaluation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.observability.dashboard.services.test_design_evaluation_service import (
    DEFAULT_TEST_DESIGN_GOLDEN_SET,
    TestDesignEvaluationReport as DesignEvaluationReport,
    load_test_design_golden_set,
    run_test_design_evaluation,
    write_test_design_evaluation_report,
)


class TestTestDesignEvaluationService:
    """Verify Golden Test Set evaluation behavior."""

    def test_load_test_design_golden_set(self) -> None:
        cases = load_test_design_golden_set(DEFAULT_TEST_DESIGN_GOLDEN_SET)

        assert len(cases) == 4
        assert cases[0].case_id == "api-login-security"
        assert cases[0].expected_focus_areas == ["功能", "异常", "安全"]
        assert cases[0].evidence[0].source_type == "api_doc"

    def test_run_test_design_evaluation_computes_core_metrics(self) -> None:
        report = run_test_design_evaluation(DEFAULT_TEST_DESIGN_GOLDEN_SET)

        assert isinstance(report, DesignEvaluationReport)
        assert report.case_count == 4
        assert report.aggregate_metrics["requirement_coverage"] >= 0.95
        assert report.aggregate_metrics["dimension_coverage"] == 1.0
        assert report.aggregate_metrics["citation_coverage"] == 1.0
        assert report.aggregate_metrics["non_empty_output"] == 1.0
        assert report.aggregate_metrics["overall_score"] >= 0.98

    def test_case_without_evidence_does_not_get_fake_citation_section(self) -> None:
        report = run_test_design_evaluation(DEFAULT_TEST_DESIGN_GOLDEN_SET)
        result = next(item for item in report.case_results if item.case_id == "web-upload-form")

        assert result.metrics["citation_coverage"] == 1.0
        assert "## 5. 关联知识片段" not in result.generated_markdown

    def test_report_rows_are_table_friendly(self) -> None:
        report = run_test_design_evaluation(DEFAULT_TEST_DESIGN_GOLDEN_SET)
        rows = report.to_rows()

        assert rows[0]["Case"] == "api-login-security"
        assert rows[0]["Overall"]
        assert rows[0]["Citation"] == "1.000"

    def test_write_report_requires_data_evaluation_directory(self, tmp_path: Path) -> None:
        report = run_test_design_evaluation(DEFAULT_TEST_DESIGN_GOLDEN_SET)

        written = write_test_design_evaluation_report(
            report,
            "data/evaluation/test_design_report.json",
            project_root=tmp_path,
        )

        assert written.exists()
        assert written.read_text(encoding="utf-8").startswith("{")

        with pytest.raises(ValueError, match="data/evaluation"):
            write_test_design_evaluation_report(
                report,
                "reports/test_design_report.json",
                project_root=tmp_path,
            )

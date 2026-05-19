"""Unit tests for deterministic test-design review."""

from __future__ import annotations

from src.observability.dashboard.services.test_design_review_service import (
    review_test_design_markdown,
)


class TestTestDesignReviewService:
    """Verify generated test-design drafts can be reviewed deterministically."""

    def test_review_good_design_has_low_risk(self) -> None:
        report = review_test_design_markdown(
            """
# API Login Test Design
## Functional
- Verify successful login returns HTTP 200 and token.
## Boundary
- Verify empty username returns field error.
## Exception
- Verify downstream timeout returns retryable error.
## Security
- Verify expired token and unauthorized role are rejected.
## Regression
- Verify response schema remains compatible with old clients.
## Evidence
- source: api_doc/login.md
            """
        )

        assert report.risk_level == "low"
        assert report.score == 100
        assert report.missing_dimensions == []
        assert report.findings == []

    def test_review_flags_missing_dimensions_and_vague_cases(self) -> None:
        report = review_test_design_markdown(
            """
# Login Test
- 测试功能是否正常。
- 验证用户体验良好。
            """,
            expected_dimensions=("functional", "boundary", "security"),
        )

        assert report.risk_level in {"medium", "high"}
        assert "boundary" in report.missing_dimensions
        assert "security" in report.missing_dimensions
        assert any(finding.category == "executability" for finding in report.findings)
        assert any(finding.category == "assertion" for finding in report.findings)

    def test_review_empty_design_is_high_risk(self) -> None:
        report = review_test_design_markdown("")

        assert report.risk_level == "high"
        assert report.score < 100
        assert report.findings[0].finding_id == "empty-draft"

"""Unit tests for requirement-test-execution traceability."""

from __future__ import annotations

from src.observability.dashboard.services.execution_history_service import (
    ExecutionHistoryRecord,
)
from src.observability.dashboard.services.traceability_service import (
    build_traceability_report,
    extract_requirement_items,
    extract_test_points,
)


def _record(scenario_id: str, status: str, created_at: str) -> ExecutionHistoryRecord:
    return ExecutionHistoryRecord(
        record_id=f"record-{scenario_id}-{status}",
        created_at=created_at,
        plan_name=scenario_id,
        adapter="api" if scenario_id.startswith("api") else "browser",
        status=status,
        base_url="http://localhost",
        dry_run=status == "dry_run",
        total_steps=2,
        passed_steps=2 if status == "passed" else 0,
        failed_steps=1 if status == "failed" else 0,
        skipped_steps=0,
        dry_run_steps=2 if status == "dry_run" else 0,
        duration_ms=12.0,
        scenario_id=scenario_id,
    )


class TestTraceabilityService:
    """Verify traceability matrix construction."""

    def test_extract_requirement_items_from_lines(self) -> None:
        requirements = extract_requirement_items(
            """
- 登录接口需要支持用户名密码认证。
- 连续五次登录失败后需要临时锁定账户。
            """
        )

        assert [item.requirement_id for item in requirements] == ["REQ-001", "REQ-002"]
        assert "登录" in requirements[0].keywords
        assert "锁定" in requirements[1].keywords

    def test_extract_test_points_keeps_dimensions(self) -> None:
        points = extract_test_points(
            """
# 接口测试设计
## 3. 测试点
### 功能
- 验证登录接口成功时返回 200 和 token。
### 安全
- 验证错误提示不泄露账号是否存在。
## 4. 回归建议
- 不应该作为测试点。
            """
        )

        assert [point.dimension for point in points] == ["功能", "安全"]
        assert points[0].point_id == "TP-001"
        assert "登录" in points[0].keywords

    def test_build_report_links_requirements_points_and_latest_execution(self) -> None:
        report = build_traceability_report(
            requirement_text=(
                "登录接口需要支持用户名密码认证，成功后返回 token。\n"
                "错误提示不能泄露账号是否存在。"
            ),
            test_design_markdown="""
# 接口测试设计
## 3. 测试点
### 功能
- 验证登录接口在正确用户名和密码下返回 200、token 和用户信息。
### 安全
- 验证登录失败提示不暴露账号是否存在，避免用户枚举风险。
            """,
            execution_records=[
                _record("api_login", "failed", "2026-05-18T08:00:00+00:00"),
                _record("api_login", "passed", "2026-05-19T08:00:00+00:00"),
            ],
        )

        assert report.requirement_count == 2
        assert report.covered_requirement_count == 2
        assert report.automated_requirement_count == 2
        assert report.passed_requirement_count == 2
        assert report.coverage_rate == 1.0
        assert report.automation_rate == 1.0
        assert all(row.latest_status == "passed" for row in report.rows)
        assert all(row.risk_level == "low" for row in report.rows)

    def test_build_report_surfaces_gaps(self) -> None:
        report = build_traceability_report(
            requirement_text="报表导出需要支持筛选条件。",
            test_design_markdown="# Empty",
            execution_records=[],
        )

        row = report.rows[0]
        assert report.coverage_rate == 0.0
        assert row.latest_status == "not_automated"
        assert row.risk_level == "high"
        assert "missing_test_design" in row.gaps
        assert "missing_automation" in row.gaps

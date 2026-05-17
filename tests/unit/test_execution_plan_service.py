"""Unit tests for execution-plan parsing."""

from __future__ import annotations

from src.observability.dashboard.services.execution_plan_service import (
    build_execution_plan,
    get_execution_preset_steps,
)


class TestExecutionPlanService:
    """Verify natural-language execution-plan parsing."""

    def test_build_plan_parses_ui_login_steps(self) -> None:
        plan = build_execution_plan(
            "UI Login Plan",
            "\n".join(
                [
                    "打开 /login",
                    "输入 用户名 = tester",
                    "输入 密码 = Passw0rd!",
                    "点击 Sign in",
                    "断言看到 Welcome Test User",
                ]
            ),
        )

        assert plan.adapter == "ui_browser_preview"
        assert plan.target == "/login"
        assert len(plan.steps) == 5
        assert [step.action for step in plan.steps] == [
            "open",
            "input",
            "input",
            "click",
            "assert_text",
        ]
        assert plan.warnings == []

    def test_build_plan_parses_api_steps(self) -> None:
        plan = build_execution_plan(
            "API Plan",
            "\n".join(
                [
                    "POST /api/login",
                    "等待 响应返回",
                    "断言看到 token",
                ]
            ),
        )

        assert plan.adapter == "api_http_preview"
        assert plan.target == "/api/login"
        assert plan.steps[0].action == "call_api"
        assert plan.steps[0].value == "POST"
        assert plan.steps[1].action == "wait"

    def test_build_plan_flags_unsupported_steps(self) -> None:
        plan = build_execution_plan(
            "Unsupported Plan",
            "\n".join(
                [
                    "打开 /login",
                    "拖拽滑块完成验证码",
                ]
            ),
        )

        assert len(plan.warnings) == 1
        assert plan.steps[1].supported is False
        assert plan.steps[1].action == "unsupported"

    def test_get_execution_preset_steps_returns_demo_flow(self) -> None:
        preset = get_execution_preset_steps("ui_login_smoke")
        assert "打开 /login" in preset
        assert "点击 Sign in" in preset

"""Unit tests for the built-in automation scenario catalog."""

from __future__ import annotations

from src.observability.dashboard.services.automation_scenario_service import (
    build_runner_command,
    get_automation_scenario,
    get_pytest_targets,
    list_automation_scenarios,
)


class TestAutomationScenarioService:
    """Verify built-in automation scenario metadata."""

    def test_list_returns_expected_demo_scenarios(self) -> None:
        scenario_ids = [scenario.scenario_id for scenario in list_automation_scenarios()]
        assert scenario_ids == ["api_login", "api_file_upload", "ui_login_smoke"]

    def test_get_scenario_returns_metadata(self) -> None:
        scenario = get_automation_scenario("api_login")
        assert scenario.category == "API"
        assert "登录接口" in scenario.name
        assert scenario.pytest_targets == ("tests/automation/test_api_login.py",)

    def test_get_pytest_targets_supports_all(self) -> None:
        targets = get_pytest_targets("all")
        assert "tests/automation/test_api_login.py" in targets
        assert "tests/automation/test_api_file_upload.py" in targets
        assert "tests/automation/test_ui_login_smoke.py" in targets

    def test_build_runner_command_uses_scenario_id(self) -> None:
        command = build_runner_command("ui_login_smoke")
        assert "--scenario ui_login_smoke" in command

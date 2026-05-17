"""Scenario catalog for the platform's built-in demo automation suites."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class AutomationScenario:
    """A built-in demo automation scenario."""

    scenario_id: str
    name: str
    category: str
    description: str
    pytest_targets: Tuple[str, ...]
    labels: Tuple[str, ...]


_SCENARIOS: Dict[str, AutomationScenario] = {
    "api_login": AutomationScenario(
        scenario_id="api_login",
        name="API: 登录接口",
        category="API",
        description="验证登录接口的成功登录与错误凭证返回。",
        pytest_targets=("tests/automation/test_api_login.py",),
        labels=("smoke", "auth", "api"),
    ),
    "api_file_upload": AutomationScenario(
        scenario_id="api_file_upload",
        name="API: 文件上传接口",
        category="API",
        description="验证文件上传接口对二进制内容和缺失文件名的处理。",
        pytest_targets=("tests/automation/test_api_file_upload.py",),
        labels=("smoke", "upload", "api"),
    ),
    "ui_login_smoke": AutomationScenario(
        scenario_id="ui_login_smoke",
        name="UI: 登录页冒烟",
        category="UI",
        description="验证登录页基础可访问性与表单提交流程。",
        pytest_targets=("tests/automation/test_ui_login_smoke.py",),
        labels=("smoke", "ui", "login"),
    ),
}


def list_automation_scenarios() -> List[AutomationScenario]:
    """Return all built-in demo scenarios in a stable order."""
    order = ("api_login", "api_file_upload", "ui_login_smoke")
    return [_SCENARIOS[scenario_id] for scenario_id in order]


def get_automation_scenario(scenario_id: str) -> AutomationScenario:
    """Return one scenario by id."""
    try:
        return _SCENARIOS[scenario_id]
    except KeyError as exc:
        available = ", ".join(sorted(_SCENARIOS))
        raise ValueError(
            f"Unknown automation scenario: {scenario_id}. Available scenarios: {available}"
        ) from exc


def get_pytest_targets(scenario_id: str) -> Tuple[str, ...]:
    """Return pytest targets for one scenario or for all demo scenarios."""
    if scenario_id == "all":
        targets: List[str] = []
        for scenario in list_automation_scenarios():
            targets.extend(scenario.pytest_targets)
        return tuple(targets)
    return get_automation_scenario(scenario_id).pytest_targets


def build_runner_command(scenario_id: str = "all") -> str:
    """Return the CLI command used to run the demo automation suite."""
    return f".\\.venv\\Scripts\\python.exe scripts\\run_automation_suite.py --scenario {scenario_id}"

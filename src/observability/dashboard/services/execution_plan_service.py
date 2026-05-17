"""Natural-language execution plan parsing for the AI test platform."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class ExecutionStep:
    """One parsed execution step."""

    index: int
    raw_text: str
    action: str
    target: str
    value: str
    supported: bool
    note: str


@dataclass(frozen=True)
class ExecutionPlan:
    """A structured execution-plan preview."""

    name: str
    adapter: str
    target: str
    steps: List[ExecutionStep]
    warnings: List[str]
    raw_input: str

    def to_rows(self) -> List[Dict[str, str]]:
        """Return rows for dashboard table rendering."""
        rows: List[Dict[str, str]] = []
        for step in self.steps:
            rows.append(
                {
                    "Index": str(step.index),
                    "Action": step.action,
                    "Target": step.target,
                    "Value": step.value,
                    "Status": "supported" if step.supported else "unsupported",
                    "Note": step.note,
                    "Raw": step.raw_text,
                }
            )
        return rows

    def to_dict(self) -> Dict[str, object]:
        """Serialize the plan for debug-style preview."""
        return {
            "name": self.name,
            "adapter": self.adapter,
            "target": self.target,
            "warnings": self.warnings,
            "steps": [asdict(step) for step in self.steps],
        }


PRESET_EXECUTION_STEPS: Dict[str, str] = {
    "api_login": "\n".join(
        [
            "POST /api/login",
            "等待 响应返回",
            "断言看到 token",
        ]
    ),
    "api_file_upload": "\n".join(
        [
            "POST /api/upload",
            "上传 demo.txt",
            "断言看到 filename",
        ]
    ),
    "ui_login_smoke": "\n".join(
        [
            "打开 /login",
            "输入 用户名 = tester",
            "输入 密码 = Passw0rd!",
            "点击 Sign in",
            "断言看到 Welcome Test User",
        ]
    ),
}


def get_execution_preset_steps(scenario_id: str) -> str:
    """Return preset natural-language steps for a known demo scenario."""
    return PRESET_EXECUTION_STEPS.get(scenario_id, "")


def _parse_supported_step(index: int, line: str) -> ExecutionStep:
    stripped = line.strip()

    open_match = re.match(r"^(?:打开|访问|open)\s+(.+)$", stripped, re.IGNORECASE)
    if open_match:
        return ExecutionStep(index, stripped, "open", open_match.group(1).strip(), "", True, "")

    http_match = re.match(
        r"^(GET|POST|PUT|DELETE|PATCH)\s+(\S+)(?:\s+(.*))?$",
        stripped,
        re.IGNORECASE,
    )
    if http_match:
        method, path, extra = http_match.groups()
        return ExecutionStep(
            index,
            stripped,
            "call_api",
            path.strip(),
            method.upper(),
            True,
            extra.strip() if extra else "",
        )

    input_match = re.match(
        r"^(?:输入|填写)\s+(.+?)(?:\s*(?:=|为|:)\s*|\s+)(.+)$",
        stripped,
        re.IGNORECASE,
    )
    if input_match:
        field_name, value = input_match.groups()
        return ExecutionStep(index, stripped, "input", field_name.strip(), value.strip(), True, "")

    click_match = re.match(r"^(?:点击|click)\s+(.+)$", stripped, re.IGNORECASE)
    if click_match:
        return ExecutionStep(index, stripped, "click", click_match.group(1).strip(), "", True, "")

    upload_match = re.match(r"^(?:上传|upload)\s+(.+)$", stripped, re.IGNORECASE)
    if upload_match:
        return ExecutionStep(index, stripped, "upload", upload_match.group(1).strip(), "", True, "")

    wait_match = re.match(r"^(?:等待|wait)\s+(.+)$", stripped, re.IGNORECASE)
    if wait_match:
        return ExecutionStep(index, stripped, "wait", wait_match.group(1).strip(), "", True, "")

    submit_match = re.match(r"^(?:提交|submit)$", stripped, re.IGNORECASE)
    if submit_match:
        return ExecutionStep(index, stripped, "submit", "current_form", "", True, "")

    assert_text_match = re.match(
        r"^(?:断言看到|验证看到|断言页面包含|assert text)\s+(.+)$",
        stripped,
        re.IGNORECASE,
    )
    if assert_text_match:
        return ExecutionStep(
            index,
            stripped,
            "assert_text",
            assert_text_match.group(1).strip(),
            "",
            True,
            "",
        )

    return ExecutionStep(
        index,
        stripped,
        "unsupported",
        "",
        "",
        False,
        "当前规则尚不支持该步骤，请在后续执行适配器阶段补充。",
    )


def _infer_adapter(steps: Sequence[ExecutionStep]) -> str:
    if any(step.action == "call_api" and step.supported for step in steps):
        return "api_http_preview"
    if any(
        step.action in {"open", "input", "click", "submit", "upload", "assert_text", "wait"}
        and step.supported
        for step in steps
    ):
        return "ui_browser_preview"
    return "generic_preview"


def _infer_target(steps: Sequence[ExecutionStep]) -> str:
    for step in steps:
        if step.action in {"open", "call_api"} and step.target:
            return step.target
    return "unspecified"


def build_execution_plan(name: str, step_text: str) -> ExecutionPlan:
    """Parse natural-language test steps into a structured execution plan."""
    normalized_name = name.strip() or "Execution Plan Preview"
    lines = [line.strip() for line in step_text.splitlines() if line.strip()]
    steps = [_parse_supported_step(index + 1, line) for index, line in enumerate(lines)]

    warnings: List[str] = []
    for step in steps:
        if not step.supported:
            warnings.append(f"Step {step.index}: {step.raw_text}")

    return ExecutionPlan(
        name=normalized_name,
        adapter=_infer_adapter(steps),
        target=_infer_target(steps),
        steps=steps,
        warnings=warnings,
        raw_input=step_text,
    )

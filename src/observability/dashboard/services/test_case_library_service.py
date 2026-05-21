"""Static test-case catalog for the interview-oriented automation platform."""

from __future__ import annotations

from dataclasses import dataclass

from src.observability.dashboard.services.automation_scenario_service import (
    build_runner_command,
)


@dataclass(frozen=True)
class TestCaseItem:
    """A dashboard-friendly automated test case."""

    case_id: str
    title: str
    test_type: str
    module: str
    priority: str
    scenario_id: str
    scenario_name: str
    automation_status: str
    pytest_target: str
    assertion: str
    related_report: str


@dataclass(frozen=True)
class ApiRequestExample:
    """A simple API request example for explaining interface testing."""

    name: str
    method: str
    path: str
    request_example: str
    expected_result: str
    related_case_id: str


_TEST_CASES: tuple[TestCaseItem, ...] = (
    TestCaseItem(
        case_id="TC-API-LOGIN-001",
        title="登录接口-正确账号密码返回认证令牌",
        test_type="接口测试",
        module="登录鉴权",
        priority="P0",
        scenario_id="api_login",
        scenario_name="API: 登录接口",
        automation_status="已自动化",
        pytest_target="tests/automation/test_api_login.py::test_api_login_success",
        assertion="响应状态为 200，响应体包含 token 和用户信息。",
        related_report="reports/junit.xml",
    ),
    TestCaseItem(
        case_id="TC-API-LOGIN-002",
        title="登录接口-错误密码返回认证失败",
        test_type="接口测试",
        module="登录鉴权",
        priority="P1",
        scenario_id="api_login",
        scenario_name="API: 登录接口",
        automation_status="已自动化",
        pytest_target="tests/automation/test_api_login.py::test_api_login_rejects_invalid_password",
        assertion="响应状态为 401，错误信息不泄露敏感账号状态。",
        related_report="reports/junit.xml",
    ),
    TestCaseItem(
        case_id="TC-API-UPLOAD-001",
        title="文件上传接口-二进制文件上传成功",
        test_type="接口测试",
        module="文件上传",
        priority="P1",
        scenario_id="api_file_upload",
        scenario_name="API: 文件上传接口",
        automation_status="已自动化",
        pytest_target="tests/automation/test_api_file_upload.py::test_api_file_upload_accepts_binary_payload",
        assertion="响应状态为 201，返回 filename 和 size。",
        related_report="reports/junit.xml",
    ),
    TestCaseItem(
        case_id="TC-API-UPLOAD-002",
        title="文件上传接口-缺少文件名时返回参数错误",
        test_type="接口测试",
        module="文件上传",
        priority="P2",
        scenario_id="api_file_upload",
        scenario_name="API: 文件上传接口",
        automation_status="已自动化",
        pytest_target="tests/automation/test_api_file_upload.py::test_api_file_upload_requires_filename_header",
        assertion="响应状态为 400，并提示 filename header 缺失。",
        related_report="reports/junit.xml",
    ),
    TestCaseItem(
        case_id="TC-UI-LOGIN-001",
        title="登录页-页面元素冒烟检查",
        test_type="界面测试",
        module="登录页面",
        priority="P1",
        scenario_id="ui_login_smoke",
        scenario_name="UI: 登录页冒烟",
        automation_status="Dry-run 已接入",
        pytest_target="tests/automation/test_ui_login_smoke.py::test_ui_login_page_smoke",
        assertion="登录页标题、用户名、密码、提交按钮可见。",
        related_report="reports/junit.xml",
    ),
    TestCaseItem(
        case_id="TC-UI-LOGIN-002",
        title="登录页-表单提交后展示欢迎信息",
        test_type="界面测试",
        module="登录页面",
        priority="P1",
        scenario_id="ui_login_smoke",
        scenario_name="UI: 登录页冒烟",
        automation_status="Dry-run 已接入",
        pytest_target="tests/automation/test_ui_login_smoke.py::test_ui_login_form_submission_succeeds",
        assertion="输入测试账号后提交，页面展示 Welcome Test User。",
        related_report="reports/junit.xml",
    ),
)


_API_REQUESTS: tuple[ApiRequestExample, ...] = (
    ApiRequestExample(
        name="登录成功",
        method="POST",
        path="/api/login",
        request_example='{"username": "tester", "password": "Passw0rd!"}',
        expected_result='HTTP 200，响应体包含 {"token": "..."}',
        related_case_id="TC-API-LOGIN-001",
    ),
    ApiRequestExample(
        name="登录失败",
        method="POST",
        path="/api/login",
        request_example='{"username": "tester", "password": "wrong"}',
        expected_result="HTTP 401，返回认证失败错误信息。",
        related_case_id="TC-API-LOGIN-002",
    ),
    ApiRequestExample(
        name="文件上传成功",
        method="POST",
        path="/api/files",
        request_example='headers={"X-Filename": "demo.txt"}, body=<binary>',
        expected_result="HTTP 201，返回 filename 和 size。",
        related_case_id="TC-API-UPLOAD-001",
    ),
    ApiRequestExample(
        name="文件上传参数错误",
        method="POST",
        path="/api/files",
        request_example="headers={}, body=<binary>",
        expected_result="HTTP 400，提示缺少文件名。",
        related_case_id="TC-API-UPLOAD-002",
    ),
)


def list_test_cases() -> list[TestCaseItem]:
    """Return the current demo test-case catalog."""
    return list(_TEST_CASES)


def list_api_request_examples() -> list[ApiRequestExample]:
    """Return API request examples linked to automated test cases."""
    return list(_API_REQUESTS)


def build_case_catalog_rows(cases: list[TestCaseItem] | None = None) -> list[dict[str, str]]:
    """Build rows suitable for Streamlit dataframes."""
    selected = cases if cases is not None else list_test_cases()
    return [
        {
            "用例ID": case.case_id,
            "标题": case.title,
            "类型": case.test_type,
            "模块": case.module,
            "优先级": case.priority,
            "场景": case.scenario_name,
            "自动化状态": case.automation_status,
            "断言": case.assertion,
            "pytest目标": case.pytest_target,
        }
        for case in selected
    ]


def build_api_request_rows() -> list[dict[str, str]]:
    """Build API request rows for display."""
    return [
        {
            "接口名称": item.name,
            "方法": item.method,
            "路径": item.path,
            "请求示例": item.request_example,
            "预期结果": item.expected_result,
            "关联用例": item.related_case_id,
        }
        for item in list_api_request_examples()
    ]


def summarize_test_cases(cases: list[TestCaseItem] | None = None) -> dict[str, int]:
    """Return high-level counts for the test-case catalog."""
    selected = cases if cases is not None else list_test_cases()
    return {
        "total": len(selected),
        "api": sum(1 for case in selected if case.test_type == "接口测试"),
        "ui": sum(1 for case in selected if case.test_type == "界面测试"),
        "automated": sum(1 for case in selected if "已" in case.automation_status),
    }


def build_scenario_execution_command(scenario_id: str) -> str:
    """Return the command used to run one scenario from the dashboard."""
    return (
        f"{build_runner_command(scenario_id)} "
        f"--junitxml reports/dashboard-{scenario_id}-junit.xml "
        f"--allure-results reports/dashboard-{scenario_id}-allure-results"
    )

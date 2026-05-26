"""Platform workspace routes inspired by full-scope testing products."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/platform", tags=["platform"])


PROJECTS: list[dict[str, Any]] = [
    {
        "project_id": "qualitypilot-demo",
        "name": "QualityPilot Demo",
        "description": "基于 MCP + RAG 的智能自动化测试平台演示项目。",
        "modules": ["登录鉴权", "文件上传", "Web 登录页", "性能压测", "失败分析"],
        "stack": ["Vue", "FastAPI", "MCP Tools", "RAG", "pytest", "Allure"],
    }
]

WEB_TEST_SCRIPTS: list[dict[str, Any]] = [
    {
        "script_id": "web-login-smoke",
        "name": "登录页冒烟测试",
        "module": "Web 登录页",
        "framework": "Playwright",
        "status": "ready",
        "priority": "P1",
        "target_url": "http://127.0.0.1:5173",
        "steps": [
            "打开登录页或演示首页",
            "输入测试账号 tester",
            "提交登录动作",
            "断言页面出现 QualityPilot 工作台",
        ],
        "assertions": ["页面标题包含 QualityPilot", "无 console error", "关键导航可见"],
        "pytest_target": "tests/automation/test_ui_login_smoke.py",
        "ai_capability": "可通过 AI 助手把自然语言步骤转换为 Playwright 脚本草稿。",
        "rag_sources": ["requirement", "test_case", "standard"],
    },
    {
        "script_id": "web-api-workbench-flow",
        "name": "接口工作台主流程",
        "module": "接口测试工作台",
        "framework": "Playwright",
        "status": "planned",
        "priority": "P2",
        "target_url": "http://127.0.0.1:5173/api-testing",
        "steps": [
            "进入接口测试工作台",
            "选择登录鉴权模块",
            "点击登录成功用例",
            "发送 Mock 请求并查看断言结果",
        ],
        "assertions": ["响应区域出现 PASS", "状态码为 200", "断言通过数为 3"],
        "pytest_target": "tests/e2e/test_api_workbench_flow.py",
        "ai_capability": "失败时可结合 DOM、接口响应和用例元数据生成修复建议。",
        "rag_sources": ["api_doc", "test_case", "test_report"],
    },
]

APP_TEST_SCRIPTS: list[dict[str, Any]] = [
    {
        "script_id": "app-login-contract",
        "name": "App 登录接口契约检查",
        "module": "移动端登录",
        "case_set": "登录鉴权",
        "platform": "Android",
        "automation_engine": "UiAutomator2 (Android)",
        "device": "Mock Android 13",
        "status": "ready",
        "priority": "P2",
        "scope": "当前先不接真机，使用接口契约和 Mock 数据模拟移动端登录链路。",
        "steps": ["构造移动端登录请求", "校验 token 和 user schema", "校验错误密码分支"],
        "assertions": ["成功返回 token", "错误密码返回 401", "不泄露敏感字段"],
        "pytest_target": "tests/automation/test_app_contract.py",
        "last_run_at": "builtin",
        "is_builtin": True,
        "ai_capability": "可根据 App 需求文档生成兼容性和弱网场景。",
    },
    {
        "script_id": "app-upload-compat",
        "name": "App 文件上传兼容性脚本",
        "module": "移动端文件上传",
        "case_set": "文件上传",
        "platform": "Android / iOS",
        "automation_engine": "Appium",
        "device": "真机云 / 模拟器",
        "status": "planned",
        "priority": "P2",
        "scope": "覆盖相册、拍照、断网重试和大文件上传兼容性。",
        "steps": ["选择本地图片", "模拟弱网重试", "校验上传结果和错误提示"],
        "assertions": ["上传成功返回 file_id", "超大文件有明确提示", "弱网重试不重复提交"],
        "pytest_target": "tests/automation/test_app_upload_contract.py",
        "last_run_at": "-",
        "is_builtin": True,
        "ai_capability": "可结合接口文档和历史 Bug 生成机型兼容性用例。",
    },
]

USER_APP_TEST_SCRIPTS: list[dict[str, Any]] = []

PERFORMANCE_SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_id": "perf-login-baseline",
        "name": "登录接口基线压测",
        "module": "登录鉴权",
        "tool": "Locust",
        "status": "ready",
        "users": 50,
        "spawn_rate": 5,
        "duration": "2m",
        "target": "POST /api/login",
        "metrics": {
            "p95_ms": 180,
            "avg_ms": 92,
            "rps": 120,
            "error_rate": "0.2%",
        },
        "risk": "关注高并发下 token 生成耗时和错误率。",
        "command": "locust -f tests/performance/locust_login.py --headless -u 50 -r 5 -t 2m",
    },
    {
        "scenario_id": "perf-upload-step-load",
        "name": "文件上传阶梯压测",
        "module": "文件上传",
        "tool": "Locust",
        "status": "planned",
        "users": 100,
        "spawn_rate": 10,
        "duration": "5m",
        "target": "POST /api/upload",
        "metrics": {
            "p95_ms": 420,
            "avg_ms": 210,
            "rps": 55,
            "error_rate": "1.1%",
        },
        "risk": "关注大文件上传、缺少文件名和超时重试。",
        "command": "locust -f tests/performance/locust_upload.py --headless -u 100 -r 10 -t 5m",
    },
]

CICD_JOBS: list[dict[str, Any]] = [
    {
        "job_id": "ci-quality-gate",
        "name": "质量门禁流水线",
        "trigger": "push / pull_request",
        "status": "ready",
        "stages": ["ruff", "pytest unit", "pytest automation", "allure artifacts"],
        "command": "ruff check src tests && pytest tests/unit -v",
        "quality_gate": "单元测试通过率 100%，自动化失败时生成失败分析和 Bug 草稿。",
    },
    {
        "job_id": "nightly-regression",
        "name": "夜间回归任务",
        "trigger": "schedule 02:00",
        "status": "planned",
        "stages": ["RAG 知识库快照", "API 回归", "Web 冒烟", "报告归档"],
        "command": "python scripts/run_automation_suite.py --scenario api_login",
        "quality_gate": "失败用例进入 AI 失败分析队列。",
    },
]

DOCUMENTS: list[dict[str, Any]] = [
    {
        "doc_id": "qualitypilot-readme",
        "title": "项目 README",
        "category": "项目说明",
        "path": "README.md",
        "purpose": "用于 GitHub 首页展示项目定位、技术栈、启动方式和演示流程。",
        "rag_ready": True,
    },
    {
        "doc_id": "interview-guide",
        "title": "测试开发面试讲解稿",
        "category": "面试文档",
        "path": "docs/interview_qa.md",
        "purpose": "解释项目功能、测试点、自动化流程、性能测试和 AI 能力。",
        "rag_ready": True,
    },
    {
        "doc_id": "mcp-tools",
        "title": "MCP Tools 说明",
        "category": "MCP 文档",
        "path": "docs/mcp_tools.md",
        "purpose": "说明 retrieve_test_context、generate_test_cases、run_api_tests 等工具。",
        "rag_ready": True,
    },
]

SETTINGS: list[dict[str, Any]] = [
    {
        "setting_id": "llm-provider",
        "name": "LLM Provider",
        "value": "demo deterministic / optional OpenAI-compatible",
        "description": "当前默认使用确定性生成，后续可接入真实大模型。",
    },
    {
        "setting_id": "rag-store",
        "name": "RAG Knowledge Store",
        "value": "local keyword demo / vector store ready",
        "description": "知识库支持 project、module、version、source_type 元数据过滤。",
    },
    {
        "setting_id": "mcp-server",
        "name": "MCP Server",
        "value": "mcp-server console script",
        "description": "暴露测试上下文检索、用例生成、执行和失败分析工具。",
    },
    {
        "setting_id": "test-runner",
        "name": "Test Runner",
        "value": "pytest + Allure artifacts",
        "description": "自动化执行结果可解析 JUnit XML，并生成 Allure 结果目录。",
    },
]


class RunRequest(BaseModel):
    """Generic run request for platform demo modules."""

    target_id: str = Field(default="")
    dry_run: bool = Field(default=True)


class SearchRequest(BaseModel):
    """Global search request."""

    keyword: str = Field(..., min_length=1)


class CopilotRequest(BaseModel):
    """Global testing copilot request."""

    message: str = Field(..., min_length=1)
    project_id: str = Field(default="qualitypilot-demo")


class AppTestScriptSaveRequest(BaseModel):
    """Request body for creating or updating one App automation script."""

    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    platform: str = Field(default="Android")
    automation_engine: str = Field(default="UiAutomator2 (Android)")
    case_set: str = Field(default="登录鉴权")
    priority: str = Field(default="P2")
    device: str = Field(default="Mock Android 13")
    status: str = Field(default="draft")
    pytest_target: str = Field(default="")
    steps: list[str] = Field(default_factory=list)
    assertions: list[str] = Field(default_factory=list)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _app_script_items() -> list[dict[str, Any]]:
    return [*APP_TEST_SCRIPTS, *USER_APP_TEST_SCRIPTS]


def _normalize_app_script_payload(
    request: AppTestScriptSaveRequest,
    *,
    script_id: str,
) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "name": request.name.strip(),
        "module": request.case_set.strip() or "APP 自动化",
        "case_set": request.case_set.strip() or "登录鉴权",
        "platform": request.platform,
        "automation_engine": request.automation_engine,
        "device": request.device,
        "status": request.status,
        "priority": request.priority,
        "scope": request.description.strip() or "自定义 APP 自动化测试脚本。",
        "steps": [step.strip() for step in request.steps if step.strip()],
        "assertions": [item.strip() for item in request.assertions if item.strip()],
        "pytest_target": request.pytest_target.strip(),
        "last_run_at": "-",
        "is_builtin": False,
        "ai_capability": "可结合 RAG 需求文档生成兼容性、弱网和异常场景。",
        "updated_at": _now(),
    }


def _run_record(
    *,
    run_id: str,
    target_id: str,
    name: str,
    module: str,
    command: str,
    status: str = "passed",
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "target_id": target_id,
        "name": name,
        "module": module,
        "status": status,
        "started_at": _now(),
        "finished_at": _now(),
        "command": command,
        "summary": {
            "total": 3,
            "passed": 3 if status == "passed" else 2,
            "failed": 0 if status == "passed" else 1,
            "duration_seconds": 1.2,
        },
        "artifacts": [
            "reports/api-runs/demo/junit.xml",
            "reports/api-runs/demo/allure-results",
            "reports/api-runs/demo/ai_failure_analysis.md",
        ],
        "ai_next_step": "如果失败，QualityPilot 会调用 analyze_failure 和 generate_bug_report MCP tools。",
    }


@router.get("/projects")
def get_projects() -> dict[str, Any]:
    """Return available platform projects."""
    return {"items": PROJECTS, "summary": {"total": len(PROJECTS)}}


@router.get("/dashboard")
def get_dashboard() -> dict[str, Any]:
    """Return dashboard statistics similar to a full testing platform."""
    return {
        "api_tests": {"total": 4, "passed": 3, "failed": 1},
        "web_tests": {"total": len(WEB_TEST_SCRIPTS), "passed": 1, "failed": 0},
        "app_tests": {
            "total": len(_app_script_items()),
            "passed": sum(1 for item in _app_script_items() if item["status"] in {"ready", "demo"}),
            "failed": 0,
        },
        "perf_tests": {"total": len(PERFORMANCE_SCENARIOS), "running": 0},
        "recent_runs": [
            {"name": "登录接口回归", "type": "api", "status": "passed", "time": "刚刚"},
            {"name": "接口工作台主流程", "type": "web", "status": "planned", "time": "10 分钟前"},
            {"name": "登录接口基线压测", "type": "performance", "status": "passed", "time": "今天"},
        ],
        "trend": [
            {"date": "05-20", "passed": 8, "failed": 1},
            {"date": "05-21", "passed": 10, "failed": 0},
            {"date": "05-22", "passed": 9, "failed": 2},
            {"date": "05-23", "passed": 12, "failed": 1},
            {"date": "05-24", "passed": 14, "failed": 1},
            {"date": "05-25", "passed": 16, "failed": 0},
            {"date": "05-26", "passed": 18, "failed": 1},
        ],
        "qualitypilot_features": [
            "MCP tools 可被 Agent 调用",
            "RAG 知识库按测试场景过滤",
            "pytest 执行结果进入 Allure/JUnit 报告",
            "失败用例可生成分析和 Bug 草稿",
        ],
    }


@router.get("/web-tests/scripts")
def get_web_test_scripts() -> dict[str, Any]:
    """Return Web automation scripts."""
    return {
        "items": WEB_TEST_SCRIPTS,
        "summary": {
            "total": len(WEB_TEST_SCRIPTS),
            "frameworks": sorted({item["framework"] for item in WEB_TEST_SCRIPTS}),
            "modules": sorted({item["module"] for item in WEB_TEST_SCRIPTS}),
        },
    }


@router.post("/web-tests/scripts/{script_id}/run")
def run_web_test_script(script_id: str, request: RunRequest | None = None) -> dict[str, Any]:
    """Run or preview one Web automation script."""
    script = next((item for item in WEB_TEST_SCRIPTS if item["script_id"] == script_id), None)
    if script is None:
        return _run_record(
            run_id=f"web-{script_id}-not-found",
            target_id=script_id,
            name="未知 Web 脚本",
            module="Web",
            command="not found",
            status="failed",
        )
    return _run_record(
        run_id=f"web-{script_id}-demo",
        target_id=script_id,
        name=script["name"],
        module=script["module"],
        command=f"pytest {script['pytest_target']}",
        status="passed" if script["status"] in {"ready", "planned"} else "failed",
    )


@router.get("/app-tests/scripts")
def get_app_test_scripts() -> dict[str, Any]:
    """Return App testing scripts or contract scenarios."""
    items = _app_script_items()
    return {
        "items": items,
        "summary": {
            "total": len(items),
            "platforms": sorted({item["platform"] for item in items}),
            "engines": sorted({item["automation_engine"] for item in items}),
            "case_sets": sorted({item["case_set"] for item in items}),
            "ready": sum(1 for item in items if item["status"] in {"ready", "demo"}),
        },
    }


@router.post("/app-tests/scripts")
def create_app_test_script(request: AppTestScriptSaveRequest) -> dict[str, Any]:
    """Create one App automation script draft."""
    script_id = f"app-custom-{len(USER_APP_TEST_SCRIPTS) + 1:03d}"
    script = _normalize_app_script_payload(request, script_id=script_id)
    USER_APP_TEST_SCRIPTS.append(script)
    return {"script": script, "message": "App 自动化脚本已创建"}


@router.put("/app-tests/scripts/{script_id}")
def update_app_test_script(script_id: str, request: AppTestScriptSaveRequest) -> dict[str, Any]:
    """Update one custom App automation script."""
    for index, script in enumerate(USER_APP_TEST_SCRIPTS):
        if script["script_id"] == script_id:
            updated = {
                **_normalize_app_script_payload(request, script_id=script_id),
                "last_run_at": script.get("last_run_at", "-"),
            }
            USER_APP_TEST_SCRIPTS[index] = updated
            return {"script": updated, "message": "App 自动化脚本已更新"}
    raise HTTPException(status_code=404, detail="只能编辑自定义 App 自动化脚本")


@router.delete("/app-tests/scripts/{script_id}")
def delete_app_test_script(script_id: str) -> dict[str, Any]:
    """Delete one custom App automation script."""
    for index, script in enumerate(USER_APP_TEST_SCRIPTS):
        if script["script_id"] == script_id:
            USER_APP_TEST_SCRIPTS.pop(index)
            return {"message": "App 自动化脚本已删除"}
    raise HTTPException(status_code=404, detail="只能删除自定义 App 自动化脚本")


@router.post("/app-tests/scripts/{script_id}/run")
def run_app_test_script(script_id: str, request: RunRequest | None = None) -> dict[str, Any]:
    """Run or preview one App test contract."""
    script = next((item for item in _app_script_items() if item["script_id"] == script_id), None)
    if script is None:
        return _run_record(
            run_id=f"app-{script_id}-not-found",
            target_id=script_id,
            name="未知 App 脚本",
            module="APP",
            command="not found",
            status="failed",
        )
    script["last_run_at"] = _now()
    return _run_record(
        run_id=f"app-{script_id}-demo",
        target_id=script_id,
        name=script["name"],
        module=script["module"],
        command=f"pytest {script.get('pytest_target') or 'tests/automation/test_app_contract.py'}",
        status="passed" if script.get("pytest_target") or script["status"] in {"ready", "demo"} else "failed",
    )


@router.get("/performance/scenarios")
def get_performance_scenarios() -> dict[str, Any]:
    """Return performance testing scenarios."""
    return {
        "items": PERFORMANCE_SCENARIOS,
        "summary": {
            "total": len(PERFORMANCE_SCENARIOS),
            "tools": sorted({item["tool"] for item in PERFORMANCE_SCENARIOS}),
            "ready": sum(1 for item in PERFORMANCE_SCENARIOS if item["status"] == "ready"),
        },
    }


@router.post("/performance/scenarios/{scenario_id}/run")
def run_performance_scenario(
    scenario_id: str, request: RunRequest | None = None
) -> dict[str, Any]:
    """Run or preview one performance scenario."""
    scenario = next(
        (item for item in PERFORMANCE_SCENARIOS if item["scenario_id"] == scenario_id),
        PERFORMANCE_SCENARIOS[0],
    )
    return {
        **_run_record(
            run_id=f"perf-{scenario_id}-demo",
            target_id=scenario_id,
            name=scenario["name"],
            module=scenario["module"],
            command=scenario["command"],
        ),
        "metrics": scenario["metrics"],
        "tool": scenario["tool"],
    }


@router.get("/cicd/jobs")
def get_cicd_jobs() -> dict[str, Any]:
    """Return CI/CD and scheduled test jobs."""
    return {
        "items": CICD_JOBS,
        "summary": {
            "total": len(CICD_JOBS),
            "ready": sum(1 for item in CICD_JOBS if item["status"] == "ready"),
        },
    }


@router.post("/cicd/jobs/{job_id}/run")
def run_cicd_job(job_id: str, request: RunRequest | None = None) -> dict[str, Any]:
    """Run or preview one CI/CD job."""
    job = next((item for item in CICD_JOBS if item["job_id"] == job_id), CICD_JOBS[0])
    return _run_record(
        run_id=f"cicd-{job_id}-demo",
        target_id=job_id,
        name=job["name"],
        module="CI/CD",
        command=job["command"],
    )


@router.get("/documents")
def get_documents() -> dict[str, Any]:
    """Return project testing documents."""
    return {
        "items": DOCUMENTS,
        "summary": {
            "total": len(DOCUMENTS),
            "rag_ready": sum(1 for item in DOCUMENTS if item["rag_ready"]),
            "categories": sorted({item["category"] for item in DOCUMENTS}),
        },
    }


@router.get("/settings")
def get_platform_settings() -> dict[str, Any]:
    """Return platform integration settings."""
    return {"items": SETTINGS, "summary": {"total": len(SETTINGS)}}


@router.post("/global-search")
def global_search(request: SearchRequest) -> dict[str, Any]:
    """Search across platform assets."""
    keyword = request.keyword.lower()
    candidates: list[dict[str, Any]] = []
    for project in PROJECTS:
        candidates.append(
            {
                "type": "project",
                "title": project["name"],
                "path": "/",
                "description": project["description"],
            }
        )
    for script in WEB_TEST_SCRIPTS:
        candidates.append(
            {
                "type": "web_test",
                "title": script["name"],
                "path": "/web-testing",
                "description": script["ai_capability"],
            }
        )
    for script in _app_script_items():
        candidates.append(
            {
                "type": "app_test",
                "title": script["name"],
                "path": "/app-testing",
                "description": script["ai_capability"],
            }
        )
    for scenario in PERFORMANCE_SCENARIOS:
        candidates.append(
            {
                "type": "performance",
                "title": scenario["name"],
                "path": "/performance",
                "description": scenario["risk"],
            }
        )
    for document in DOCUMENTS:
        candidates.append(
            {
                "type": "document",
                "title": document["title"],
                "path": "/documents",
                "description": document["purpose"],
            }
        )
    items = [
        item
        for item in candidates
        if keyword in item["title"].lower() or keyword in item["description"].lower()
    ]
    return {"items": items, "summary": {"total": len(items), "keyword": request.keyword}}


@router.post("/copilot/chat")
def copilot_chat(request: CopilotRequest) -> dict[str, Any]:
    """Return a deterministic platform copilot response."""
    message = request.message.strip()
    operations = []
    if "性能" in message or "压测" in message:
        operations.append({"type": "open_page", "path": "/performance", "reason": "需要查看性能场景"})
        operations.append({"type": "run_scenario", "target": "perf-login-baseline"})
    elif "失败" in message or "bug" in message.lower():
        operations.append({"type": "retrieve_test_context", "target": "test_report/log/bug"})
        operations.append({"type": "generate_bug_report", "target": "failed_cases"})
    elif "接口" in message or "api" in message.lower():
        operations.append({"type": "open_page", "path": "/api-testing", "reason": "需要进入接口测试工作台"})
        operations.append({"type": "generate_test_cases", "target": "selected_endpoint"})
    else:
        operations.append({"type": "global_search", "target": message})
    return {
        "message": message,
        "answer": "我已按 QualityPilot 的测试开发工作流生成操作计划。真实执行时会调用 MCP tools、RAG 检索和 pytest/Allure 链路。",
        "operations": operations,
        "recommended_tools": [
            "retrieve_test_context",
            "generate_test_cases",
            "run_api_tests",
            "analyze_failure",
            "generate_bug_report",
        ],
    }


@router.get("/workspace")
def get_platform_workspace() -> dict[str, Any]:
    """Return a single payload for the full platform workspace."""
    return {
        "project": PROJECTS[0],
        "web_tests": WEB_TEST_SCRIPTS,
        "app_tests": _app_script_items(),
        "performance": PERFORMANCE_SCENARIOS,
        "cicd": CICD_JOBS,
        "documents": DOCUMENTS,
        "settings": SETTINGS,
        "differentiation": [
            "FullScopeTest 偏通用测试管理，QualityPilot 增加 MCP tools 可被 Agent 调用。",
            "QualityPilot 的知识库按 project/module/version/source_type 过滤，支撑 RAG 测试上下文检索。",
            "自动化结果可进入失败分析和 Bug 报告生成闭环。",
        ],
    }

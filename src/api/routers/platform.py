"""Platform workspace routes inspired by full-scope testing products."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

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
        "platform": "Android / iOS 接口层",
        "status": "demo",
        "priority": "P2",
        "scope": "当前先不接真机，使用接口契约和 Mock 数据模拟移动端登录链路。",
        "steps": ["构造移动端登录请求", "校验 token 和 user schema", "校验错误密码分支"],
        "assertions": ["成功返回 token", "错误密码返回 401", "不泄露敏感字段"],
        "ai_capability": "可根据 App 需求文档生成兼容性和弱网场景。",
    }
]

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


@router.get("/projects")
def get_projects() -> dict[str, Any]:
    """Return available platform projects."""
    return {"items": PROJECTS, "summary": {"total": len(PROJECTS)}}


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


@router.get("/app-tests/scripts")
def get_app_test_scripts() -> dict[str, Any]:
    """Return App testing scripts or contract scenarios."""
    return {"items": APP_TEST_SCRIPTS, "summary": {"total": len(APP_TEST_SCRIPTS)}}


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


@router.get("/workspace")
def get_platform_workspace() -> dict[str, Any]:
    """Return a single payload for the full platform workspace."""
    return {
        "project": PROJECTS[0],
        "web_tests": WEB_TEST_SCRIPTS,
        "app_tests": APP_TEST_SCRIPTS,
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

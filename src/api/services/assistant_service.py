"""AI testing assistant service for the Vue/FastAPI platform."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.api.services.knowledge_service import search_knowledge_contexts
from src.api.services.model_config_service import (
    current_model_metadata,
    generate_with_text_model,
    is_text_model_enabled,
)
from src.mcp_server.tools.analyze_failure import analyze_failure_payload
from src.mcp_server.tools.generate_bug_report import generate_bug_report_payload
from src.mcp_server.tools.generate_test_cases import generate_test_cases_payload


@dataclass(frozen=True)
class PromptTemplate:
    """Prompt template metadata displayed by the AI assistant page."""

    template_id: str
    name: str
    category: str
    description: str
    recommended_tools: tuple[str, ...]
    default_source_types: tuple[str, ...]
    placeholder: str


PROMPT_TEMPLATES: tuple[PromptTemplate, ...] = (
    PromptTemplate(
        template_id="test_case_generation",
        name="智能用例生成",
        category="test_design",
        description="根据需求或接口说明生成结构化测试用例，覆盖功能、异常、边界、安全和回归。",
        recommended_tools=("retrieve_test_context", "generate_test_cases"),
        default_source_types=("requirement", "api_doc", "test_case", "bug", "standard"),
        placeholder="例如：登录接口支持账号密码登录，成功返回 token，失败返回 401。",
    ),
    PromptTemplate(
        template_id="api_test_design",
        name="接口测试设计",
        category="api_testing",
        description="围绕 API method、path、body、headers 和断言设计接口测试点。",
        recommended_tools=("retrieve_test_context", "generate_test_cases", "run_api_tests"),
        default_source_types=("api_doc", "requirement", "standard", "bug"),
        placeholder="例如：POST /api/upload 上传二进制文件，需要校验文件名和大小。",
    ),
    PromptTemplate(
        template_id="failure_analysis",
        name="失败原因分析",
        category="failure_triage",
        description="把失败日志、断言错误或 JUnit 信息整理成原因分类、证据和修复建议。",
        recommended_tools=("retrieve_test_context", "analyze_failure"),
        default_source_types=("test_report", "log", "bug", "api_doc", "standard"),
        placeholder="例如：test_api_login_success 失败，AssertionError: expected token but missing。",
    ),
    PromptTemplate(
        template_id="bug_report",
        name="Bug 报告生成",
        category="defect",
        description="把失败分析结果转换为可提交到缺陷平台的结构化 Bug 草稿。",
        recommended_tools=("analyze_failure", "generate_bug_report"),
        default_source_types=("test_report", "log", "bug", "requirement", "api_doc"),
        placeholder="例如：登录成功接口返回 200，但响应体缺少 token 字段。",
    ),
    PromptTemplate(
        template_id="testability_review",
        name="可测性分析",
        category="review",
        description="评估需求是否具备可测试性，指出缺失字段、验收标准、边界和风险。",
        recommended_tools=("retrieve_test_context", "generate_test_cases"),
        default_source_types=("requirement", "api_doc", "standard"),
        placeholder="例如：用户可以上传文件，系统需要进行安全检查。",
    ),
)


LOCAL_CONTEXTS: tuple[dict[str, Any], ...] = (
    {
        "chunk_id": "CTX-AUTH-001",
        "source_id": "api_authentication.md",
        "source_type": "api_doc",
        "title": "API Document: Authentication",
        "content": (
            "POST /api/login expects username and password. Success returns 200 with token and user. "
            "Invalid credentials return 401. Missing required fields return 400."
        ),
        "score": 0.92,
        "metadata": {"project": "QualityPilot", "module": "登录鉴权", "version": "demo"},
    },
    {
        "chunk_id": "CTX-STD-001",
        "source_id": "test_standard_api_error_handling.md",
        "source_type": "standard",
        "title": "Test Standard: API Error Handling",
        "content": (
            "API tests should cover status code, response schema, error code, error message, trace id, "
            "authorization failures, boundary values, and sensitive information leakage."
        ),
        "score": 0.88,
        "metadata": {"project": "QualityPilot", "module": "测试规范", "version": "demo"},
    },
    {
        "chunk_id": "CTX-BUG-001",
        "source_id": "defect_login_lockout.md",
        "source_type": "bug",
        "title": "Defect: Login Lockout Counter Reset",
        "content": (
            "Regression checks: successful login resets failure counter; lockout is per account; "
            "audit logs include account id, client ip, and timestamp."
        ),
        "score": 0.81,
        "metadata": {"project": "QualityPilot", "module": "登录鉴权", "version": "demo"},
    },
    {
        "chunk_id": "CTX-UPLOAD-001",
        "source_id": "api_upload_demo.md",
        "source_type": "api_doc",
        "title": "API Document: File Upload",
        "content": (
            "POST /api/upload accepts binary body with X-Filename header. Success returns 201 with filename "
            "and size. Missing filename returns 400 missing_filename."
        ),
        "score": 0.86,
        "metadata": {"project": "QualityPilot", "module": "文件上传", "version": "demo"},
    },
)


def list_prompt_templates() -> list[dict[str, Any]]:
    """Return prompt templates for the AI assistant UI."""
    return [asdict(template) for template in PROMPT_TEMPLATES]


def get_prompt_template(template_id: str) -> PromptTemplate:
    """Return one prompt template by id."""
    for template in PROMPT_TEMPLATES:
        if template.template_id == template_id:
            return template
    available = ", ".join(template.template_id for template in PROMPT_TEMPLATES)
    raise ValueError(f"Unknown template_id: {template_id}. Available: {available}")


async def build_assistant_response(
    *,
    template_id: str,
    message: str,
    project: str = "QualityPilot",
    module: str = "",
    version: str = "demo",
    use_knowledge: bool = True,
    source_types: list[str] | None = None,
    top_k: int = 4,
) -> dict[str, Any]:
    """Build an assistant response using deterministic MCP-style capabilities."""
    template = get_prompt_template(template_id)
    user_message = _validate_message(message)
    contexts = retrieve_local_contexts(
        query=user_message,
        source_types=source_types or list(template.default_source_types),
        project=project,
        module=module,
        version=version,
        top_k=top_k,
    ) if use_knowledge else []

    if template_id in {"test_case_generation", "api_test_design"}:
        payload = await generate_test_cases_payload(
            requirement=user_message,
            project=project,
            module=module or None,
            version=version or None,
            source_types=list(source_types or template.default_source_types),
            contexts=contexts,
            case_count=6,
            top_k=top_k,
        )
        result_type = "test_cases"
        markdown = _test_cases_markdown(payload)
    elif template_id == "failure_analysis":
        payload = _failure_analysis_from_message(user_message, contexts, project, module, version)
        result_type = "failure_analysis"
        markdown = _failure_markdown(payload)
    elif template_id == "bug_report":
        analysis_payload = _failure_analysis_from_message(user_message, contexts, project, module, version)
        payload = generate_bug_report_payload(
            analyses=analysis_payload["analyses"],
            project=project,
            module=module,
            version=version,
            environment="local",
            reporter="QualityPilot",
            include_non_bug_candidates=True,
            include_markdown=True,
        )
        result_type = "bug_report"
        markdown = payload.get("markdown", "")
    else:
        payload = _testability_review(user_message, contexts, project, module, version)
        result_type = "testability_review"
        markdown = _testability_markdown(payload)

    llm_result = _maybe_refine_with_real_model(
        template=template,
        message=user_message,
        contexts=contexts,
        deterministic_markdown=markdown,
    )
    if llm_result.get("used_model") and llm_result.get("content"):
        markdown = str(llm_result["content"])

    return {
        "template": asdict(template),
        "message": user_message,
        "project": project,
        "module": module,
        "version": version,
        "use_knowledge": use_knowledge,
        "contexts": contexts,
        "result_type": result_type,
        "result": payload,
        "markdown": markdown,
        "model_config": current_model_metadata(),
        "llm_call": llm_result,
        "recommended_next_steps": _recommended_next_steps(result_type),
    }


def _maybe_refine_with_real_model(
    *,
    template: PromptTemplate,
    message: str,
    contexts: list[dict[str, Any]],
    deterministic_markdown: str,
) -> dict[str, Any]:
    """Use the configured real model when enabled, otherwise keep deterministic output."""
    if not is_text_model_enabled():
        return {
            "ok": False,
            "used_model": False,
            "message": "未启用真实模型，使用本地确定性生成。",
        }
    context_text = "\n\n".join(
        f"[{item.get('source_type')}] {item.get('title')}\n{item.get('content')}"
        for item in contexts[:4]
    )
    prompt = (
        f"任务类型：{template.name}\n"
        f"用户输入：{message}\n\n"
        f"RAG 上下文：\n{context_text or '无'}\n\n"
        f"本地工具已生成的草稿：\n{deterministic_markdown}\n\n"
        "请在保留结构化信息的基础上，生成更自然、完整、适合测试开发面试讲解的中文结果。"
    )
    return generate_with_text_model(prompt)


def retrieve_local_contexts(
    *,
    query: str,
    source_types: list[str],
    project: str = "QualityPilot",
    module: str = "",
    version: str = "demo",
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Return deterministic local RAG-like contexts for interview demos."""
    return search_knowledge_contexts(
        query=query,
        project=project,
        module=module,
        version=version,
        source_types=source_types,
        top_k=top_k,
    )


def _failure_analysis_from_message(
    message: str,
    contexts: list[dict[str, Any]],
    project: str,
    module: str,
    version: str,
) -> dict[str, Any]:
    failed_case = {
        "case_id": "FC-ASSISTANT-001",
        "classname": "assistant.input",
        "name": _shorten(message, 48),
        "status": "failure",
        "message": message,
        "details": message,
        "duration_seconds": 0.0,
        "failure_category": "assistant_input",
        "failure_signature": _shorten(message, 160),
    }
    return analyze_failure_payload(
        failed_cases=[failed_case],
        contexts=contexts,
        project=project,
        module=module,
        version=version,
        analysis_depth="standard",
    )


def _testability_review(
    message: str,
    contexts: list[dict[str, Any]],
    project: str,
    module: str,
    version: str,
) -> dict[str, Any]:
    risks = []
    if not any(word in message for word in ("状态码", "返回", "响应", "字段", "错误码")):
        risks.append("缺少明确的接口响应、状态码或字段验收标准")
    if not any(word in message for word in ("异常", "失败", "错误", "边界", "权限")):
        risks.append("缺少异常、边界或权限场景描述")
    if not any(word in message for word in ("日志", "追踪", "trace", "审计")):
        risks.append("缺少日志、trace id 或审计要求")

    return {
        "project": project,
        "module": module,
        "version": version,
        "requirement": message,
        "score": max(40, 100 - len(risks) * 18),
        "risks": risks,
        "missing_acceptance_criteria": [
            "成功路径的输入、输出和状态变更",
            "失败路径的错误码、错误信息和数据一致性",
            "安全和权限约束",
            "可观测性要求：日志、trace id、审计字段",
        ],
        "suggested_questions": [
            "接口成功和失败分别返回哪些状态码？",
            "哪些字段是必填、可选、敏感字段？",
            "异常场景是否需要记录审计日志？",
            "是否存在幂等、并发、权限或频控要求？",
        ],
        "contexts": contexts,
    }


def _test_cases_markdown(payload: dict[str, Any]) -> str:
    lines = ["# 测试用例草稿", ""]
    for case in payload.get("test_cases", []):
        lines.extend(
            [
                f"## {case['case_id']} {case['title']}",
                f"- 维度：{case['dimension']}",
                f"- 优先级：{case['priority']}",
                "- 步骤：",
            ]
        )
        lines.extend(f"  {index}. {step}" for index, step in enumerate(case.get("steps", []), start=1))
        lines.append("- 预期结果：")
        lines.extend(f"  - {result}" for result in case.get("expected_results", []))
        lines.append("")
    return "\n".join(lines).strip()


def _failure_markdown(payload: dict[str, Any]) -> str:
    lines = ["# 失败分析草稿", ""]
    for analysis in payload.get("analyses", []):
        lines.extend(
            [
                f"## {analysis['analysis_id']} {analysis['name']}",
                f"- 根因类型：{analysis['root_cause_type']}",
                f"- 置信度：{analysis['confidence']}",
                f"- 可能原因：{analysis['likely_root_cause']}",
                "- 建议修复：",
            ]
        )
        lines.extend(f"  - {item}" for item in analysis.get("suggested_fix", []))
        lines.append("")
    return "\n".join(lines).strip()


def _testability_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 可测性分析",
        "",
        f"- 分数：{payload['score']}",
        "",
        "## 风险",
    ]
    risks = payload.get("risks", [])
    lines.extend(f"- {risk}" for risk in risks) if risks else lines.append("- 暂无明显风险")
    lines.extend(["", "## 建议补充的问题"])
    lines.extend(f"- {question}" for question in payload.get("suggested_questions", []))
    return "\n".join(lines).strip()


def _recommended_next_steps(result_type: str) -> list[str]:
    mapping = {
        "test_cases": ["review_test_cases", "map_cases_to_pytest", "run_api_tests"],
        "failure_analysis": ["confirm_reproducibility", "generate_bug_report", "rerun_failed_case"],
        "bug_report": ["review_bug_draft", "attach_reports", "submit_to_issue_tracker"],
        "testability_review": ["clarify_requirement", "add_acceptance_criteria", "generate_test_cases"],
    }
    return mapping.get(result_type, ["review_output"])


def _validate_message(message: str) -> str:
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message cannot be empty")
    return message.strip()


def _tokens(text: str) -> set[str]:
    normalized = []
    for char in text.lower():
        normalized.append(char if char.isalnum() else " ")
    return {token for token in "".join(normalized).split() if len(token) >= 2}


def _shorten(text: str, max_length: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_length else text[:max_length].rstrip() + "..."

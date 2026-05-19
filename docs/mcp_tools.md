# QualityPilot MCP Tools

QualityPilot exposes MCP tools for RAG retrieval and test-development workflows.
The current goal is to keep the existing knowledge-base tools while adding
structured context retrieval and test case generation for the core testing
workflow.

## Existing Tools

| Tool | Purpose | Main Inputs | Output |
| --- | --- | --- | --- |
| `query_knowledge_hub` | Search the RAG knowledge base with optional metadata filters. | `query`, `collection`, `project`, `module`, `version`, `source_types`, `top_k` | Markdown plus structured JSON containing `query`, `contexts`, `source_id`, `source_type`, `title`, `content`, `score`, and `metadata`. |
| `list_collections` | List ChromaDB collections. | `include_stats` | Markdown collection summary. |
| `get_document_summary` | Find and summarize chunks for a document. | `doc_id`, `collection` | Markdown document summary. |
| `retrieve_test_context` | Retrieve test-oriented RAG context for downstream testing tasks. | `query`, `project`, `module`, `version`, `source_types`, `top_k` | Structured JSON with `query`, `contexts`, and `recommended_usage`. |
| `generate_test_cases` | Generate structured test cases from a requirement and optional RAG context. | `requirement`, `project`, `module`, `version`, `source_types`, `dimensions`, `case_count`, `top_k` | Structured JSON with `test_cases`, `context_summary`, priorities, steps, expected results, and pytest automation hints. |
| `run_api_tests` | Run API automation scenarios and write test reports. | `scenario_id`, `base_url`, `dry_run`, `execution_mode`, `step_text`, `junitxml`, `allure_results`, `record_history` | Structured JSON with `run_id`, status summary, step results, logs, and report paths. |

## Source Type Metadata

Chunks can be tagged with these source types:

```text
requirement
api_doc
db_schema
test_case
bug
test_report
log
standard
```

The ingestion chunk metadata also reserves these fields for test-development
filtering:

```json
{
  "project": "qualitypilot-demo",
  "module": "auth",
  "version": "v1",
  "source_type": "api_doc",
  "source_id": "auth-api-v1"
}
```

## retrieve_test_context

### Purpose

`retrieve_test_context` is the preferred tool when an AI Agent needs testing
evidence before producing test cases, analyzing failed executions, or drafting a
bug report. It reuses the existing knowledge retrieval pipeline but returns a
test-friendly JSON payload.

### Input Example

```json
{
  "query": "登录接口密码错误时应该如何校验",
  "project": "qualitypilot-demo",
  "module": "auth",
  "version": "v1",
  "source_types": ["requirement", "api_doc", "bug"],
  "top_k": 5
}
```

### Output Example

```json
{
  "query": "登录接口密码错误时应该如何校验",
  "contexts": [
    {
      "chunk_id": "auth-api-v1_0000_8f1a2b3c",
      "source_id": "auth-api-v1",
      "source_type": "api_doc",
      "title": "登录接口说明",
      "content": "密码错误时返回 401，并提示账号或密码错误。",
      "score": 0.8732,
      "metadata": {
        "project": "qualitypilot-demo",
        "module": "auth",
        "version": "v1",
        "source_type": "api_doc",
        "source_id": "auth-api-v1"
      }
    }
  ],
  "recommended_usage": [
    "test_case_generation",
    "failure_analysis",
    "bug_report_generation"
  ]
}
```

## generate_test_cases

### Purpose

`generate_test_cases` turns a requirement into reviewable test cases. It first
tries to retrieve RAG context, then produces deterministic JSON test cases with
dimensions, priorities, steps, expected results, citations, and pytest file
suggestions.

This stage does not require an LLM key. It is a stable baseline for interview
demo and can later be upgraded to call an LLM with a JSON schema.

### Input Example

```json
{
  "requirement": "登录接口密码错误时返回 401，并提示账号或密码错误",
  "project": "qualitypilot-demo",
  "module": "auth",
  "version": "v1",
  "source_types": ["requirement", "api_doc", "bug"],
  "dimensions": ["functional", "negative", "security"],
  "case_count": 3,
  "top_k": 5
}
```

### Output Example

```json
{
  "requirement": "登录接口密码错误时返回 401，并提示账号或密码错误",
  "generation_strategy": "rule_based_with_rag_context",
  "dimensions": ["functional", "negative", "security"],
  "test_cases": [
    {
      "case_id": "TC-001",
      "title": "登录接口密码错误时返回 401，并提示账号或密码错误 主流程验证",
      "dimension": "functional",
      "priority": "P1",
      "preconditions": ["测试环境可访问", "基础测试数据已准备"],
      "steps": ["按需求描述准备合法输入数据", "执行目标接口或页面操作", "检查业务状态、响应字段和持久化结果"],
      "expected_results": ["实际结果符合需求描述", "关键字段和状态正确", "相关日志可追踪"],
      "automation_hint": {
        "suggested_layer": "api",
        "pytest_marker": "automation",
        "suggested_file": "pytest_tests/api/test_qualitypilot_demo_auth.py"
      },
      "citations": [
        {
          "chunk_id": "auth-api-v1_0000_8f1a2b3c",
          "source_id": "auth-api-v1",
          "source_type": "api_doc",
          "title": "登录接口说明",
          "score": 0.8732
        }
      ]
    }
  ],
  "context_summary": {
    "context_count": 1,
    "source_type_distribution": {
      "api_doc": 1
    },
    "recommended_usage": ["test_case_generation", "failure_analysis", "bug_report_generation"]
  }
}
```

## run_api_tests

### Purpose

`run_api_tests` executes API-oriented scenarios after test cases are generated
and reviewed. It supports two modes:

- `plan`: parse API steps, execute them through the API adapter, and emit JUnit /
  Allure-compatible reports.
- `pytest`: run the built-in API pytest automation scenario. When `dry_run` is
  true, it only returns the pytest command arguments.

The default is `plan` + `dry_run=true`, so the tool is safe to demo without a
real backend service.

### Input Example

```json
{
  "scenario_id": "api_login",
  "base_url": "http://127.0.0.1:8000",
  "dry_run": true,
  "execution_mode": "plan",
  "junitxml": "reports/mcp-api-login-junit.xml",
  "allure_results": "reports/mcp-api-login-allure-results",
  "record_history": false
}
```

### Output Example

```json
{
  "run_id": "api-api_login-1a2b3c4d",
  "scenario_id": "api_login",
  "execution_mode": "plan",
  "adapter": "api_http",
  "base_url": "http://127.0.0.1:8000",
  "dry_run": true,
  "status": "dry_run",
  "summary": {
    "total": 3,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "dry_run": 3
  },
  "steps": [
    {
      "index": 1,
      "action": "call_api",
      "status": "dry_run",
      "message": "Dry run only; no network request was sent",
      "request_method": "POST",
      "request_url": "http://127.0.0.1:8000/api/login"
    }
  ],
  "report_paths": {
    "junitxml": "reports/mcp-api-login-junit.xml",
    "allure_results": "reports/mcp-api-login-allure-results",
    "allure_result": "reports/mcp-api-login-allure-results/<uuid>-result.json"
  }
}
```

### Workflow Position

```text
文档入库
  -> retrieve_test_context
  -> generate_test_cases
  -> run_api_tests
  -> get_test_report
  -> analyze_failure
  -> generate_bug_report
```

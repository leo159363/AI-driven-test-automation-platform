# QualityPilot MCP Tools

QualityPilot exposes MCP tools for RAG retrieval and test-development workflows.
The first-stage goal is to keep the existing knowledge-base tools while adding
structured context retrieval for test case generation, failure analysis, and bug
report generation.

## Existing Tools

| Tool | Purpose | Main Inputs | Output |
| --- | --- | --- | --- |
| `query_knowledge_hub` | Search the RAG knowledge base with optional metadata filters. | `query`, `collection`, `project`, `module`, `version`, `source_types`, `top_k` | Markdown plus structured JSON containing `query`, `contexts`, `source_id`, `source_type`, `title`, `content`, `score`, and `metadata`. |
| `list_collections` | List ChromaDB collections. | `include_stats` | Markdown collection summary. |
| `get_document_summary` | Find and summarize chunks for a document. | `doc_id`, `collection` | Markdown document summary. |
| `retrieve_test_context` | Retrieve test-oriented RAG context for downstream testing tasks. | `query`, `project`, `module`, `version`, `source_types`, `top_k` | Structured JSON with `query`, `contexts`, and `recommended_usage`. |

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

# AI Test Platform Design

## Overview

本设计把现有 RAG/MCP 工程重定位为“AI 驱动的自动化测试平台”。第一版不重写底层架构，而是复用已有能力：

- Streamlit Dashboard 作为可视化入口。
- RAG ingestion 和 hybrid search 作为测试知识库能力。
- Evaluation panel 和 pytest 作为质量回归能力。
- MCP server 作为后续对外工具协议和自动化执行扩展点。

设计原则：

- 先形成测试开发面试可讲的闭环，再扩展完整平台功能。
- 保留原 RAG/MCP 的工程深度，不把项目降级成纯页面 demo。
- 测试工作台输出“测试设计草稿”，不伪装成已经完成完整 ALM/TestOps 系统。
- 后续自然语言自动化执行以独立 adapter 接入，避免污染测试设计逻辑。

## Architecture

```text
User
  |
  v
Streamlit Dashboard
  |
  +-- Test Workbench Page
  |     |
  |     +-- Scenario Templates
  |     +-- Draft Builder
  |     +-- Knowledge Retrieval Client
  |     +-- Markdown Export
  |
  +-- Data Browser
  +-- Ingestion Manager
  +-- Ingestion Traces
  +-- Query Traces
  +-- Evaluation Panel
        |
        v
Existing RAG / MCP Core
  |
  +-- Ingestion Pipeline
  +-- Hybrid Search
  +-- Vector Store
  +-- BM25 Index
  +-- Evaluators
  +-- MCP Tools
```

## Components

### 1. Test Workbench Page

Current file:

- `src/observability/dashboard/pages/test_workbench.py`

Responsibilities:

- Collect requirement text.
- Select a high-level testing scenario.
- Select focus areas.
- Optionally retrieve related knowledge snippets.
- Generate a structured Markdown draft.
- Export the draft.

Current implementation keeps generation deterministic and template-based. This is intentional for Stage 1/2 because it gives stable tests and avoids depending on external LLM calls during basic smoke tests.

Future extraction:

- Move scenario templates to `src/observability/dashboard/services/test_design_templates.py`.
- Move draft generation to `src/observability/dashboard/services/test_design_service.py`.
- Keep Streamlit page focused on UI rendering.

### 2. Scenario Template Registry

Current scenarios are platform-level testing workflows:

- Requirement document analysis
- API test design
- Web UI automation planning
- Knowledge-base augmentation
- Regression evaluation

Each template contains:

- `summary`
- default focus dimensions
- sections by focus dimension
- recommended testing layers
- regression suggestions

This avoids hard-coding a specific business project into the platform positioning.

### 3. Knowledge Retrieval Client

Current function:

- `_fetch_knowledge_hits()`

Current behavior:

- Loads settings.
- Tries to create existing Hybrid Search.
- Searches by user query and selected collection.
- Converts results into lightweight `KnowledgeHit` records.
- Degrades gracefully when retrieval is unavailable.

Future behavior:

- Move retrieval into a service class.
- Add query trace logging for test workbench generation.
- Add source filtering by document type: PRD, defect, API doc, test standard.

### 4. Draft Builder

Current function:

- `_build_test_outline()`

Output:

- Markdown test design draft.

Sections:

- Testing background
- Recommended testing layers
- Test points
- Regression suggestions
- Related knowledge snippets
- Notes

Future behavior:

- Add JSON output for downstream automation.
- Add LLM-assisted expansion behind a provider interface.
- Add quality checks for duplicate, empty, or unsupported test points.

### 5. Evaluation

Existing files:

- `src/observability/dashboard/pages/evaluation_panel.py`
- `src/observability/evaluation/*`
- `tests/fixtures/golden_test_set.json`
- `tests/e2e/test_recall.py`

Stage 2 keeps existing RAG evaluation intact. Later stages can add test-design-specific metrics:

- requirement coverage
- focus dimension coverage
- duplicate case rate
- unsupported assertion rate
- citation coverage

### 6. Test Report Center

New files:

- `src/observability/dashboard/pages/test_reports.py`
- `src/observability/dashboard/services/test_report_service.py`

Responsibilities:

- Discover common local report artifacts produced by pytest and Allure.
- Parse JUnit XML and display a lightweight execution summary.
- Show whether Allure result directories and HTML report directories already exist.
- Keep report viewing separate from the future execution adapter.

Current stage behavior:

- Supports `pytest --junitxml=...` generated XML summaries.
- Detects `allure-results/` and `allure-report/` style directories.
- Does not attempt to launch an Allure web server inside the dashboard.

### 7. Automation Execution Adapter

Not implemented in Stage 2.

Reserved design:

```text
Generated Test Step
  -> Step Parser
  -> Execution Plan
  -> Adapter
       +-- Playwright
       +-- MCP browser tools
       +-- API test runner
  -> Execution Report
```

The adapter boundary prevents browser execution concerns from mixing with RAG retrieval and test design generation.

## Data Models

### KnowledgeHit

```python
@dataclass
class KnowledgeHit:
    chunk_id: str
    source_path: str
    score: float
    snippet: str
```

### TestDesignDraft

Future service-level model:

```python
@dataclass
class TestDesignDraft:
    scenario: str
    requirement: str
    focus_areas: list[str]
    markdown: str
    evidence: list[KnowledgeHit]
    warnings: list[str]
```

### TestExecutionSummary

```python
@dataclass
class TestExecutionSummary:
    source_path: Path
    suite_name: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: float
```

### ExecutionPlan

Future automation model:

```python
@dataclass
class ExecutionPlan:
    name: str
    target: str
    steps: list[dict]
    adapter: str
```

## Error Handling

- Empty requirement: generate from scenario template.
- Empty focus areas: use scenario defaults.
- Knowledge retrieval unavailable: warn and continue.
- Empty retrieval result: warn and avoid fake citations.
- Export without draft: show empty-state message.
- Missing local config or vector store: do not crash the dashboard page.

## Testing Strategy

### Current Stage Tests

- `tests/unit/test_dashboard_config.py`
  - Dashboard config service import and workbench page import.
- `tests/e2e/test_dashboard_smoke.py`
  - Streamlit page smoke rendering, including Test Workbench.
- `tests/e2e/test_mcp_client.py::TestMCPClientE2E::test_initialize_and_tools_list`
  - MCP server still initializes and lists tools after project rename.

### Future Tests

- Unit tests for template registry.
- Unit tests for draft generation.
- Unit tests for retrieval fallback behavior.
- E2E test for generating a draft with and without knowledge snippets.
- Evaluation regression for retrieval quality.
- Adapter contract tests for future Playwright/MCP execution.

## Commit and Release Plan

- Stage 1: project rename and positioning.
- Stage 2: formal spec.
- Stage 3: extract test design logic into services and unit tests.
- Stage 4: add a test report center for JUnit and Allure artifacts.
- Stage 5: add knowledge-source taxonomy and ingestion examples.
- Stage 6: add test-design evaluation metrics.
- Stage 7: add automation execution planning.
- Stage 8: add Playwright or MCP browser execution adapter.

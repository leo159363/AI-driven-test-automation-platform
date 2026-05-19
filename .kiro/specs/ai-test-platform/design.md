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
- Add source filtering by document type: requirement, API doc, defect, test standard, execution log.

### 3.1 Knowledge Source Taxonomy

Current files:

- `src/observability/dashboard/services/test_design_service.py`
- `tests/fixtures/test_knowledge_sources/*`

Responsibilities:

- Normalize source types into `requirement`, `api_doc`, `defect`, `test_standard`, `execution_log`, or `unknown`.
- Prefer explicit ingestion metadata fields such as `source_type`, `document_type`, `doc_type`, `type`, or `category`.
- Fall back to path, title, summary, and tags when explicit metadata is missing.
- Display the human-readable source type in Test Workbench retrieval results and generated drafts.
- Keep fixture documents generic so the platform is not tied to any legacy business project.

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

Stage 7 adds deterministic test-design evaluation without requiring a live LLM:

- `tests/fixtures/test_design_golden_set.json`
- `src/observability/dashboard/services/test_design_evaluation_service.py`
- `scripts/evaluate_test_design.py`

The evaluator generates drafts through the existing test-design service and computes:

- `requirement_coverage`: expected requirement keywords found in the generated draft.
- `dimension_coverage`: expected focus dimensions included as generated sections.
- `citation_coverage`: expected evidence sources present, with no fake citation section when no evidence is expected.
- `non_empty_output`: generated Markdown is not empty.
- `overall_score`: average of the core metrics.

Reports are printed by default. JSON reports are written only when the CLI receives an explicit `--output` path under `data/evaluation/`, which remains ignored by default.

Stage 12 exposes the same deterministic evaluator in the dashboard:

- `src/observability/dashboard/pages/test_design_evaluation.py`

The page loads the Golden Test Set, previews cases, runs evaluation on demand, displays aggregate metrics and per-case rows, and can explicitly save a JSON report under `data/evaluation/`.

Stage 17 adds deterministic review checks for a single generated test-design draft:

- `src/observability/dashboard/services/test_design_review_service.py`
- `src/observability/dashboard/pages/test_design_review.py`

The review service complements Golden Test Set evaluation. Golden Set answers "does the generator regress on known requirements"; the review service answers "is this specific draft actionable enough for a tester to execute." It checks:

- missing expected dimensions such as functional, boundary, exception, security, and regression;
- vague descriptions that are too broad to automate;
- subjective or untestable assertions;
- weak assertion wording;
- missing source or evidence references.

The dashboard page lets the user paste or reuse Markdown, choose expected dimensions, and view score, risk level, covered dimensions, missing dimensions, table findings, and JSON output.

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
- Supports execution-plan JUnit XML summaries generated by the API execution adapter report writer.
- Detects `allure-results/`, execution-plan Allure result directories, and `allure-report/` style directories.
- Does not attempt to launch an Allure web server inside the dashboard.

### 7. Demo Automation Scenario Catalog

New files:

- `src/observability/dashboard/pages/automation_scenarios.py`
- `src/observability/dashboard/services/automation_scenario_service.py`
- `scripts/run_automation_suite.py`
- `tests/automation/*`

Responsibilities:

- Define a small, stable set of built-in demo automation scenarios.
- Keep the scenario list visible inside the dashboard so the platform does not look limited to one example.
- Provide a single CLI runner that can execute one scenario or the whole demo suite.
- Produce JUnit XML by default and Allure artifacts when the plugin is installed.

Current stage behavior:

- Demo scenarios cover API login, API file upload, and UI login smoke.
- The tests run against a deterministic local HTTP fixture, not an external business system.
- The dashboard shows the scenario catalog, while execution still happens via CLI.

### 8. Automation Execution Planning

New files:

- `src/observability/dashboard/pages/execution_planner.py`
- `src/observability/dashboard/services/execution_plan_service.py`

Responsibilities:

- Parse natural-language test steps into structured execution steps.
- Infer a preview adapter type such as API HTTP or UI browser preview.
- Keep execution planning visible in the dashboard before real adapters are connected.
- Surface unsupported steps as warnings instead of pretending they are executable.

Current stage behavior:

- Supports a deterministic rule-based parser for common API and UI test steps.
- Provides preset step text for built-in demo automation scenarios.
- Shows a structured table and JSON-style execution-plan preview in the dashboard.
- API plans can be executed through the API HTTP adapter or previewed through dry-run mode.
- UI plans can be previewed through the Browser UI adapter dry-run and optionally executed with Playwright.

Reserved adapter boundary:

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

### 9. API Execution Adapter

New file:

- `src/observability/dashboard/services/api_execution_adapter.py`

Responsibilities:

- Execute `call_api`, `wait`, `upload`, and `assert_text` steps from an `ExecutionPlan`.
- Keep API execution behind an adapter so browser execution can be added later without rewriting planning logic.
- Support dry-run mode, which returns step results without sending network traffic.
- Capture status, step logs, HTTP status, response preview, artifacts field, and failure reason.
- Use deterministic default request bodies for the built-in demo API login and file-upload scenarios.

Current stage behavior:

- The execution planner page exposes API dry-run and API execution controls for API plans.
- The adapter uses Python standard-library HTTP calls to avoid adding runtime dependencies.
- Browser/UI actions are skipped by the API adapter and handled by the Browser UI adapter.

### 10. Browser UI Execution Adapter

New file:

- `src/observability/dashboard/services/browser_execution_adapter.py`

Responsibilities:

- Execute UI-oriented `open`, `input`, `click`, `submit`, `upload`, `wait`, and `assert_text` steps from an `ExecutionPlan`.
- Support dry-run mode without requiring Playwright to be installed.
- Keep Playwright as an optional dependency so API/report/evaluation tests remain lightweight.
- Capture failure screenshots under `reports/screenshots/` where possible and expose the path through `ExecutionResult.artifacts`.
- Reuse the same `ExecutionResult` and `ExecutionStepResult` models as the API adapter.

Current stage behavior:

- The execution planner page exposes Browser UI dry-run controls for UI plans.
- The CLI can run `ui_login_smoke` through the browser adapter in dry-run mode and write reports.
- Real browser execution is available when the optional `browser` extra and Chromium browser are installed.

### 11. Execution Result Report Writer

New files:

- `src/observability/dashboard/services/execution_result_report_service.py`
- `scripts/run_execution_plan.py`

Responsibilities:

- Convert `ExecutionResult` objects into JUnit XML so execution plans can be consumed by the existing Test Report Center.
- Mark failed steps as JUnit failures and skipped or dry-run steps as JUnit skipped cases.
- Convert `ExecutionResult` objects into minimal Allure-compatible result JSON when explicitly requested.
- Provide a CLI path for running a built-in execution plan and writing `reports/execution-plan-junit.xml`.
- Keep reporting output explicit and local; generated reports stay ignored by repository hygiene rules.

### 12. Continuous Integration

New file:

- `.github/workflows/ci.yml`

Responsibilities:

- Run the platform's core regression suite on pushes and pull requests targeting `main`.
- Install project runtime and dev dependencies in a clean GitHub-hosted Python environment.
- Generate `reports/ci-junit.xml` from pytest so failures remain consumable by report tooling.
- Generate execution-plan dry-run artifacts, including JUnit XML and Allure results.
- Upload the `reports/` directory as a CI artifact for inspection after each run.

Current stage behavior:

- CI uses Python 3.11 on `ubuntu-latest`.
- CI does not require secrets or external services.
- Browser UI execution remains in dry-run mode in CI, so Playwright browser installation is not required.

### 13. Execution History

New files:

- `src/observability/dashboard/services/execution_history_service.py`
- `src/observability/dashboard/pages/execution_history.py`

Responsibilities:

- Persist execution-plan summaries as JSONL records under `data/execution_history/`.
- Record plan name, scenario id, adapter, status, step counts, failure reason, artifacts, and report paths.
- Let the execution planner save a history record after API or UI execution.
- Let the execution-plan CLI append a record through `--record-history`.
- Display recent records and aggregate status counts in the dashboard.

Current stage behavior:

- History writes are explicit, not automatic.
- Generated history stays ignored by default because `data/` is ignored.
- CI writes a workflow artifact history file under `reports/execution-history.jsonl`.
- The history page derives quality trends from saved records: daily status counts, pass/failure/dry-run rates, adapter distribution, and top failure reasons.

### 14. Traceability Matrix

New files:

- `src/observability/dashboard/services/traceability_service.py`
- `src/observability/dashboard/pages/traceability_matrix.py`

Responsibilities:

- Extract requirement items from line-based or sentence-based user input.
- Extract bullet test points from the generated Markdown `测试点` section while preserving dimensions such as 功能, 边界, 异常, 安全, 回归, 性能, 界面, 兼容, 易用, 弱网, and 并发.
- Link requirements to test points through deterministic keyword overlap.
- Link requirements to built-in automation scenarios through domain keywords and scenario metadata.
- Use execution history records to show the latest status for matched scenarios.
- Surface coverage gaps such as missing test design, missing automation, automation not run, dry-run only, or latest execution failed.

Current stage behavior:

- The page can reuse `tw_requirement` and `tw_draft` from the Test Workbench session state.
- If no workbench data exists, the page provides a login/API sample so it can still be demonstrated.
- The matrix displays requirement count, test-design coverage rate, automation-link rate, passed-execution rate, table rows, details, and JSON output.
- The implementation is deterministic and local; it does not depend on external LLM calls.

## Data Models

### KnowledgeHit

```python
@dataclass
class KnowledgeHit:
    chunk_id: str
    source_path: str
    score: float
    snippet: str
    source_type: str
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

### TestDesignEvaluationReport

```python
@dataclass
class TestDesignEvaluationReport:
    test_set_path: str
    version: str
    case_results: list[TestDesignCaseResult]
    aggregate_metrics: dict[str, float]
    total_elapsed_ms: float
```

### TestDesignReviewReport

```python
@dataclass
class TestDesignReviewReport:
    risk_level: str
    score: int
    covered_dimensions: list[str]
    missing_dimensions: list[str]
    findings: list[TestDesignReviewFinding]
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

Current preview model:

```python
@dataclass
class ExecutionPlan:
    name: str
    adapter: str
    target: str
    steps: list[ExecutionStep]
    warnings: list[str]
    raw_input: str
```

```python
@dataclass
class ExecutionStep:
    index: int
    raw_text: str
    action: str
    target: str
    value: str
    supported: bool
    note: str
```

### ExecutionResult

Current adapter result model:

```python
@dataclass
class ExecutionResult:
    plan_name: str
    adapter: str
    base_url: str
    dry_run: bool
    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    dry_run_steps: int
    step_results: list[ExecutionStepResult]
    failure_reason: str | None
    logs: list[str]
    artifacts: dict[str, str]
```

### TraceabilityReport

```python
@dataclass
class TraceabilityReport:
    requirement_count: int
    covered_requirement_count: int
    automated_requirement_count: int
    passed_requirement_count: int
    rows: list[TraceabilityRow]
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
- `tests/unit/test_test_design_review_service.py`
  - Deterministic test-design review checks for covered dimensions, vague wording, untestable assertions, and empty drafts.
- `tests/unit/test_traceability_service.py`
  - Requirement extraction, test-point extraction, execution-history linkage, and gap detection.
- `tests/e2e/test_dashboard_smoke.py`
  - Streamlit page smoke rendering, including Test Workbench, Test Design Review, and Traceability Matrix.
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
- Stage 5: add built-in demo automation scenarios and a unified runner.
- Stage 6: add knowledge-source taxonomy and ingestion examples.
- Stage 7: add test-design evaluation metrics.
- Stage 8: add automation execution planning and preview.
- Stage 9: add API HTTP execution adapter and reserve browser execution for a later stage.
- Stage 10: document interview delivery and demo flow.
- Stage 11: export execution results as JUnit XML.
- Stage 12: expose test-design evaluation in the dashboard.
- Stage 13: add Browser UI execution adapter and Allure result export.
- Stage 14: add GitHub Actions CI and report artifact upload.
- Stage 15: add execution history and test task records.
- Stage 16: add execution quality trends and failure reason analysis.
- Stage 17: add test-design review checks and interview testing answer documentation.
- Stage 18: add requirements-to-test-to-execution traceability matrix.

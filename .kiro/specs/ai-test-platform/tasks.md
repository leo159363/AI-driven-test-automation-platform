# AI Test Platform Tasks

## Stage 1: Project Positioning

- [x] Rename the project surface to "AI 驱动的自动化测试平台".
- [x] Update README positioning for test-development interviews.
- [x] Expose Test Workbench in the Streamlit dashboard.
- [x] Update package metadata and MCP server display name.
- [x] Run dashboard smoke tests and MCP initialize smoke test.
- [x] Commit and push Stage 1.

## Stage 2: Spec Definition

- [x] Add `.kiro/specs/ai-test-platform/requirements.md`.
- [x] Add `.kiro/specs/ai-test-platform/design.md`.
- [x] Add `.kiro/specs/ai-test-platform/tasks.md`.
- [x] Record Stage 2 in `docs/development_log.md`.
- [x] Run existing smoke tests.
- [x] Commit and push Stage 2.

## Stage 3: Test Design Service Extraction

- [x] Create `src/observability/dashboard/services/test_design_service.py`.
- [x] Move `KnowledgeHit` and draft-building logic out of the Streamlit page.
- [x] Create `src/observability/dashboard/services/test_design_templates.py`.
- [x] Keep Streamlit page focused on rendering and user actions.
- [x] Add unit tests for draft generation.
- [x] Add unit tests for empty requirement and empty focus fallback.
- [x] Add unit tests that verify no fake citations are produced when evidence is empty.
- [x] Run unit and dashboard smoke tests.
- [x] Commit with Stage 3 explanation.

## Stage 4: Test Report Center

- [x] Add `src/observability/dashboard/services/test_report_service.py`.
- [x] Add `src/observability/dashboard/pages/test_reports.py`.
- [x] Add JUnit XML summary parsing for pytest execution reports.
- [x] Add local Allure results/report directory discovery.
- [x] Register the Test Reports page in the Streamlit dashboard.
- [x] Add unit tests for JUnit parsing and report artifact discovery.
- [x] Add dashboard smoke coverage for the Test Reports page.
- [x] Run unit and dashboard smoke tests.
- [x] Commit with Stage 4 explanation.

## Stage 5: Demo Automation Scenarios

- [x] Add built-in automation scenario metadata for representative API and UI flows.
- [x] Add a dashboard page to show the built-in automation scenario catalog.
- [x] Add a CLI runner that executes one or all built-in scenarios and outputs JUnit XML.
- [x] Add optional Allure output when `allure-pytest` is installed.
- [x] Add deterministic local demo automation tests for API login, file upload, and UI login smoke.
- [x] Add unit tests for the scenario catalog service.
- [x] Add dashboard smoke coverage for the automation scenarios page.
- [x] Run demo automation scenarios and regression tests.
- [x] Commit with Stage 5 explanation.

## Stage 6: Knowledge Source Taxonomy

- [x] Define knowledge source types: requirement, API doc, defect, test standard, execution log.
- [x] Add source-type metadata handling where ingestion metadata is available.
- [x] Update Test Workbench retrieval UI to show source type when available.
- [x] Add fixture documents for generic testing knowledge, not business-specific legacy data.
- [x] Add tests for retrieval result rendering and source metadata fallback.
- [x] Commit with Stage 6 explanation.

## Stage 7: Test Design Evaluation

- [x] Define a small Golden Test Set for generic requirement-to-test-design scenarios.
- [x] Add metrics for requirement coverage, dimension coverage, citation coverage, and empty output.
- [x] Add a CLI or dashboard action to run test-design evaluation.
- [x] Save evaluation report under `data/evaluation/` only when explicitly generated.
- [x] Ensure generated reports are ignored unless intentionally committed as fixtures.
- [x] Commit with Stage 7 explanation.

## Stage 8: Automation Execution Planning

- [x] Define `ExecutionPlan` data model.
- [x] Add parser for natural-language test steps into structured actions.
- [x] Add UI section that displays execution plan preview.
- [x] Keep execution preview separate from real browser execution.
- [x] Add tests for step parsing and unsupported action handling.
- [x] Commit with Stage 8 explanation.

## Stage 9: Execution Adapter

- [x] Choose first execution adapter: API HTTP adapter, with browser execution reserved for a later stage.
- [x] Implement adapter interface.
- [x] Add dry-run mode.
- [x] Add execution result model with status, logs, artifacts, and failure reason.
- [x] Add at least one local deterministic execution test.
- [x] Commit with Stage 9 explanation.

## Stage 10: Interview Delivery Documentation

- [x] Rewrite README around the current AI test platform capability set.
- [x] Add quick-start commands for dashboard, automation scenarios, evaluation, and regression tests.
- [x] Document completed stages and repository hygiene rules.
- [x] Add an interview guide with demo flow, talking points, high-frequency questions, and resume wording.
- [x] Commit with Stage 10 explanation.

## Stage 11: Execution Result Report Export

- [x] Add a JUnit XML writer for execution adapter results.
- [x] Add a CLI that runs built-in execution plans and writes JUnit XML.
- [x] Let the execution planner page save adapter results as JUnit XML.
- [x] Update the report center discovery list for execution-plan JUnit output.
- [x] Add tests that parse the generated JUnit XML through the report service.
- [x] Commit with Stage 11 explanation.

## Stage 12: Test Design Evaluation Dashboard

- [x] Add a dashboard page for deterministic test-design evaluation.
- [x] Register the page in Streamlit navigation.
- [x] Display Golden Test Set preview, aggregate metrics, per-case rows, and generated markdown details.
- [x] Allow explicit JSON report saving under `data/evaluation/`.
- [x] Add import and smoke tests for the new page.
- [x] Commit with Stage 12 explanation.

## Stage 13: Browser UI Adapter and Allure Export

- [x] Add a Browser UI execution adapter for UI-oriented execution plans.
- [x] Support browser dry-run without requiring Playwright.
- [x] Keep real Playwright execution behind an optional dependency.
- [x] Capture failure screenshot artifacts where possible.
- [x] Let the execution planner page run UI plans through the browser adapter.
- [x] Extend the execution-plan CLI with adapter selection, UI dry-run, screenshot directory, and optional Allure results output.
- [x] Convert execution adapter results into minimal Allure-compatible result JSON.
- [x] Update the report center discovery list for execution-plan Allure results.
- [x] Add focused unit tests for browser adapter behavior, Allure output, and UI CLI dry-run.
- [x] Commit with Stage 13 explanation.

## Stage 14: GitHub Actions CI

- [x] Add `.github/workflows/ci.yml`.
- [x] Run the core regression suite on push and pull request to `main`.
- [x] Generate pytest JUnit XML under `reports/ci-junit.xml`.
- [x] Generate execution-plan dry-run JUnit XML and Allure results.
- [x] Upload `reports/` as a CI artifact.
- [x] Add README CI badge and CI usage notes.
- [x] Document CI behavior in the spec and development log.
- [x] Commit with Stage 14 explanation.

## Stage 15: Execution History and Test Task Records

- [x] Add an execution history service backed by JSONL storage.
- [x] Build history records from adapter execution results.
- [x] Persist scenario id, adapter, status, step counts, failure reason, artifacts, and report paths.
- [x] Add CLI `--record-history` and `--history-path` options.
- [x] Let the execution planner save execution history records explicitly.
- [x] Add an `Execution History` dashboard page.
- [x] Register the page in Streamlit navigation.
- [x] Include execution history in CI report artifacts.
- [x] Add unit and dashboard smoke tests for history behavior.
- [x] Commit with Stage 15 explanation.

## Stage 16: Execution Quality Trends

- [x] Add quality-trend aggregation for execution history records.
- [x] Compute pass rate, failure rate, and dry-run rate.
- [x] Compute daily status rows for trend charts.
- [x] Compute adapter distribution and top failure reasons.
- [x] Render trend metrics, chart, and distribution tables in the Execution History page.
- [x] Add unit tests for trend aggregation.
- [x] Re-run dashboard smoke coverage for the history page.
- [x] Commit with Stage 16 explanation.

## Stage 17: Test Design Review and Interview Testing Answers

- [x] Add a deterministic test-design review service.
- [x] Check missing dimensions, vague descriptions, untestable assertions, weak assertions, and missing evidence.
- [x] Add a dashboard page for reviewing generated test-design Markdown.
- [x] Register the page in Streamlit navigation.
- [x] Add unit tests for review scoring and findings.
- [x] Add dashboard import and smoke tests for the new page.
- [x] Add `docs/interview_testing_answers.md` for interview questions about test cases, automation testing, and performance testing.
- [x] Re-run the staged regression suite.
- [x] Commit with Stage 17 explanation.

## Stage 18: Traceability Matrix

- [x] Add a traceability service for requirement, test-point, automation, and execution-status linkage.
- [x] Extract requirement items from lines, bullets, and short sentence separators.
- [x] Extract Markdown test points while preserving testing dimensions.
- [x] Link requirements to built-in automation scenarios through deterministic keyword overlap.
- [x] Use execution history to show latest matched scenario status.
- [x] Add a Traceability Matrix dashboard page.
- [x] Register the page in Streamlit navigation.
- [x] Add unit tests and dashboard smoke coverage.
- [x] Include traceability and test-design review tests in CI.
- [x] Commit with Stage 18 explanation.

## Stage 19: Traceability Export and Review Status

- [x] Add per-requirement traceability review statuses.
- [x] Add service-level Markdown export for traceability review material.
- [x] Add service-level CSV export for spreadsheet-style analysis.
- [x] Add dashboard review-status selectors.
- [x] Add dashboard download buttons for Markdown and CSV.
- [x] Add unit tests for status application and export output.
- [x] Re-run the staged regression suite.
- [x] Commit with Stage 19 explanation.

## Repository Hygiene

- [ ] Do not commit plaintext API keys.
- [ ] Do not commit local vector databases, cache directories, reports, or experimental exports.
- [ ] Keep unrelated legacy experiment files out of the AI test platform commit path unless explicitly reworked into generic fixtures.
- [ ] Before each commit, check `git status --short` and stage only files relevant to the current stage.

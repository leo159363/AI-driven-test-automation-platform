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

## Repository Hygiene

- [ ] Do not commit plaintext API keys.
- [ ] Do not commit local vector databases, cache directories, reports, or experimental exports.
- [ ] Keep unrelated legacy experiment files out of the AI test platform commit path unless explicitly reworked into generic fixtures.
- [ ] Before each commit, check `git status --short` and stage only files relevant to the current stage.

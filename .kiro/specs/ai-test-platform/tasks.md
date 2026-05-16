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

- [ ] Create `src/observability/dashboard/services/test_design_service.py`.
- [ ] Move `KnowledgeHit` and draft-building logic out of the Streamlit page.
- [ ] Create `src/observability/dashboard/services/test_design_templates.py`.
- [ ] Keep Streamlit page focused on rendering and user actions.
- [ ] Add unit tests for draft generation.
- [ ] Add unit tests for empty requirement and empty focus fallback.
- [ ] Add unit tests that verify no fake citations are produced when evidence is empty.
- [ ] Run unit and dashboard smoke tests.
- [ ] Commit with Stage 3 explanation.

## Stage 4: Knowledge Source Taxonomy

- [ ] Define knowledge source types: requirement, API doc, defect, test standard, execution log.
- [ ] Add source-type metadata handling where ingestion metadata is available.
- [ ] Update Test Workbench retrieval UI to show source type when available.
- [ ] Add fixture documents for generic testing knowledge, not business-specific legacy data.
- [ ] Add tests for retrieval result rendering and source metadata fallback.
- [ ] Commit with Stage 4 explanation.

## Stage 5: Test Design Evaluation

- [ ] Define a small Golden Test Set for generic requirement-to-test-design scenarios.
- [ ] Add metrics for requirement coverage, dimension coverage, citation coverage, and empty output.
- [ ] Add a CLI or dashboard action to run test-design evaluation.
- [ ] Save evaluation report under `data/evaluation/` only when explicitly generated.
- [ ] Ensure generated reports are ignored unless intentionally committed as fixtures.
- [ ] Commit with Stage 5 explanation.

## Stage 6: Automation Execution Planning

- [ ] Define `ExecutionPlan` data model.
- [ ] Add parser for natural-language test steps into structured actions.
- [ ] Add UI section that displays execution plan preview.
- [ ] Keep execution preview separate from real browser execution.
- [ ] Add tests for step parsing and unsupported action handling.
- [ ] Commit with Stage 6 explanation.

## Stage 7: Execution Adapter

- [ ] Choose first execution adapter: Playwright or MCP browser tools.
- [ ] Implement adapter interface.
- [ ] Add dry-run mode.
- [ ] Add execution result model with status, logs, artifacts, and failure reason.
- [ ] Add at least one local deterministic execution test.
- [ ] Commit with Stage 7 explanation.

## Repository Hygiene

- [ ] Do not commit plaintext API keys.
- [ ] Do not commit local vector databases, cache directories, reports, or experimental exports.
- [ ] Keep unrelated legacy experiment files out of the AI test platform commit path unless explicitly reworked into generic fixtures.
- [ ] Before each commit, check `git status --short` and stage only files relevant to the current stage.

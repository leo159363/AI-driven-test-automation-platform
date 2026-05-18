# Development Log

## Stage 1 - Project Positioning

Commit goal: rename and reposition the project as an AI-driven automation testing platform.

Scope:
- Rename the public project title to "AI 驱动的自动化测试平台".
- Keep the existing RAG, MCP, Dashboard, pytest and evaluation architecture.
- Make the Test Workbench the first visible product capability for test-development interviews.
- Keep local plaintext API keys out of the staged GitHub commit.

Out of scope:
- Full spec implementation.
- Playwright/MCP natural-language execution.
- Large test-case management features such as project/user/permission workflows.

Next stage:
- Add `.kiro/specs/ai-test-platform/requirements.md`, `design.md`, and `tasks.md`.

## Stage 2 - Formal Spec

Commit goal: define the product requirements, architecture design, and staged implementation tasks for the AI-driven automation testing platform.

Scope:
- Add Kiro-style spec files under `.kiro/specs/ai-test-platform/`.
- Keep the scope focused on requirement intake, test design generation, RAG knowledge augmentation, export, evaluation, observability, and future execution adapters.
- Avoid binding the platform to legacy or unrelated business datasets.

Out of scope:
- Service extraction.
- New runtime features.
- Browser or API execution implementation.

Verification:
- Run dashboard config tests, dashboard smoke tests, and MCP initialization smoke test.

## Stage 3 - Test Design Service Extraction

Commit goal: move test-design draft generation out of the Streamlit page and lock the behavior with focused unit tests.

Scope:
- Add reusable scenario templates and test-design draft generation services.
- Keep `test_workbench.py` focused on UI rendering, state handling, and user actions.
- Add unit tests for draft generation, fallback behavior, and evidence-free output.

Out of scope:
- Source-type taxonomy for ingestion metadata.
- Golden test set for test-design evaluation.
- Real browser execution planning or adapters.

Verification:
- Run the new test-design service unit tests.
- Re-run dashboard smoke tests and MCP initialize smoke test.
- Result: `25 passed`.

## Stage 4 - Test Report Center

Commit goal: add a dashboard report center that can summarize pytest JUnit XML reports and surface local Allure artifacts.

Scope:
- Add a report service for JUnit parsing and report discovery.
- Add a Test Reports dashboard page.
- Register the page in dashboard navigation.
- Add unit tests and dashboard smoke coverage.

Out of scope:
- Executing pytest from the dashboard.
- Launching an Allure web server.
- Real browser or API execution adapters.

Verification:
- Run the new report-service unit tests.
- Re-run dashboard smoke tests and MCP initialize smoke test.
- Result: `27 passed`.

## Stage 5 - Demo Automation Scenarios

Commit goal: add multiple built-in demo automation scenarios plus a unified runner so the platform can demonstrate more than one test target.

Scope:
- Add a scenario catalog service and dashboard page.
- Add deterministic local API and UI automation scenarios.
- Add a CLI runner that outputs JUnit XML and optional Allure artifacts.
- Add unit tests for scenario metadata and dashboard smoke coverage.

Out of scope:
- Real browser execution adapters.
- Running automation directly from the dashboard.
- Knowledge-source taxonomy work.

Verification:
- Run the demo automation tests directly.
- Run the automation runner to produce report artifacts.
- Re-run dashboard smoke tests and MCP initialize smoke test.
- Result: `39 passed`.
- Generated local report artifact: `reports/junit.xml`.

## Stage 6 - Knowledge Source Taxonomy

Commit goal: classify retrieved knowledge so the test workbench can distinguish requirements, API docs, defects, standards, and execution logs.

Scope:
- Add source-type normalization and fallback inference in the test-design service layer.
- Show source type labels in Test Workbench retrieval results and generated drafts.
- Add generic fixture documents for requirement, API document, defect, test standard, and execution log sources.
- Add unit tests for metadata preference, path fallback, rendering titles, and fixture coverage.

Out of scope:
- Source-type filtering in the retrieval query itself.
- Re-ingesting existing local vector databases.
- Business-specific legacy fixture promotion.

Verification:
- Run test-design service unit tests.
- Re-run dashboard config tests, dashboard smoke tests, and MCP initialize smoke test.
- Result: `58 passed`.

## Stage 7 - Test Design Evaluation

Commit goal: add deterministic quality evaluation for requirement-to-test-design generation.

Scope:
- Add a generic test-design Golden Test Set for API, UI, RAG knowledge, and regression-evaluation scenarios.
- Add a service that computes requirement coverage, dimension coverage, citation coverage, non-empty output, and overall score.
- Add a CLI entry point for running the test-design evaluation.
- Allow JSON report writing only when explicitly requested under `data/evaluation/`.
- Add unit tests for loading, scoring, fake-citation prevention, row output, and report path safety.

Out of scope:
- LLM-as-judge scoring for generated test cases.
- Persisting reports automatically from the dashboard.
- Committing generated evaluation reports.

Verification:
- Run test-design evaluation service unit tests.
- Run `python scripts/evaluate_test_design.py`.
- Re-run test-design, source taxonomy, API adapter, execution plan, automation scenario, report-service, dashboard smoke, and MCP initialize tests.
- Result: `63 passed`.

## Stage 8 - Automation Execution Planning

Commit goal: turn natural-language test steps into a structured execution-plan preview and expose it in the dashboard.

Scope:
- Add execution-plan data models and a rule-based step parser.
- Add an execution planner dashboard page.
- Reuse built-in demo scenarios as preset natural-language step flows.
- Add tests for supported parsing, unsupported-step warnings, and page rendering.

Out of scope:
- Real browser execution.
- API or browser adapters that actually run the plan.
- Knowledge-source taxonomy and evaluation work.

Verification:
- Run execution-plan unit tests.
- Re-run automation scenarios, report-service tests, dashboard smoke tests, and MCP initialize smoke test.
- Result: `45 passed`.

## Stage 9 - API Execution Adapter

Commit goal: connect API execution plans to a real adapter while keeping browser execution as a later extension.

Scope:
- Add an API HTTP execution adapter with dry-run and real execution modes.
- Add execution result models with status, step logs, response preview, artifacts field, and failure reason.
- Connect the execution planner dashboard page to the API adapter.
- Add deterministic local tests for API login, file upload, dry-run, and failed assertion behavior.

Out of scope:
- Playwright or MCP browser execution.
- Persisting execution reports from the dashboard.
- Running arbitrary user-authenticated external systems.

Verification:
- Run API adapter unit tests.
- Re-run execution-plan tests, automation scenarios, report-service tests, dashboard smoke tests, and MCP initialize smoke test.
- Result: `49 passed`.

## Stage 10 - Interview Delivery Documentation

Commit goal: make the GitHub repository readable as an AI-driven automation testing platform for test-development interviews.

Scope:
- Rewrite `README.md` around the current platform capabilities, not the original generic RAG project narrative.
- Add quick-start commands for Dashboard, automation scenarios, test-design evaluation, and core regression tests.
- Document completed stages and repository hygiene expectations.
- Add `docs/interview_guide.md` with demo flow, project talking points, high-frequency interview questions, resume wording, and limits that should not be overstated.

Out of scope:
- New runtime features.
- Browser execution adapter implementation.
- Changing local configuration or legacy experiment files.

Verification:
- Run documentation-adjacent dashboard import and smoke tests.
- Result: `26 passed`.

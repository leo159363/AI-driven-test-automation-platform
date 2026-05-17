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

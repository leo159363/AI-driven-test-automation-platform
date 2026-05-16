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

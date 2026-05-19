# AI Test Platform Requirements

## Introduction

本规格定义“AI 驱动的自动化测试平台”的第一版产品能力。平台面向测试开发岗位展示，目标不是一次性做完整企业级测试管理系统，而是先跑通一个可讲、可测、可扩展的闭环：

需求输入 -> 测试知识检索 -> 测试点生成 -> Markdown 导出 -> 回归评估 -> 后续自动化执行规划。

系统复用现有 Modular RAG MCP Server 的 RAG、MCP、Dashboard、pytest、evaluation 和 observability 能力，在此基础上把产品定位转向测试开发场景。

## Requirements

### Requirement 1: Requirement Intake

**User Story:** 作为测试开发工程师，我希望输入需求描述、接口说明或测试目标，让系统生成结构化测试设计草稿。

#### Acceptance Criteria

1. WHEN 用户打开测试工作台 THEN the system SHALL show a requirement input area, scenario selector, focus-area selector, knowledge collection input, and generation action.
2. WHEN 用户输入一段需求文本 THEN the system SHALL preserve the original requirement text in the generated draft.
3. WHEN 用户未输入需求文本 THEN the system SHALL generate a draft from the selected scenario template and clearly mark that no extra requirement was provided.
4. WHEN 用户选择测试关注维度 THEN the system SHALL generate sections only for selected dimensions where the scenario provides content.
5. IF 用户未选择任何关注维度 THEN the system SHALL fall back to the scenario default dimensions.

### Requirement 2: Structured Test Design Generation

**User Story:** 作为测试开发工程师，我希望系统按功能、边界、异常、安全、并发、回归等维度生成测试点，减少手工梳理成本。

#### Acceptance Criteria

1. WHEN 用户点击生成测试点 THEN the system SHALL produce a Markdown draft.
2. The generated draft SHALL include testing background, recommended testing layers, test points, regression suggestions, and notes.
3. The generated draft SHALL separate test points by testing dimension.
4. The generated draft SHALL include common supplemental cases derived from the requirement text.
5. The generated draft SHALL avoid claiming that it has executed real automation unless an execution module has actually run.

### Requirement 3: Knowledge-Augmented Test Design

**User Story:** 作为测试开发工程师，我希望平台能检索历史缺陷、测试规范、业务规则和项目文档，并把相关片段作为测试设计依据。

#### Acceptance Criteria

1. WHEN auto retrieval is enabled and a query is provided THEN the system SHALL call the existing hybrid search capability.
2. WHEN retrieval succeeds THEN the system SHALL show up to the selected Top-K knowledge snippets with source path, score, chunk id, and snippet text.
3. WHEN retrieval succeeds during draft generation THEN the system SHALL append related knowledge snippets to the generated Markdown draft.
4. IF the knowledge base is unavailable THEN the system SHALL show a readable warning and still generate a template-based draft.
5. IF no relevant knowledge is found THEN the system SHALL show an empty-result message and SHALL NOT fabricate citations.
6. The platform SHALL normalize knowledge source types into requirement, API doc, defect, test standard, execution log, or unknown.
7. WHEN retrieved metadata includes source type or document type THEN the system SHALL display the normalized source type.
8. WHEN source-type metadata is missing THEN the system SHALL infer a best-effort source type from source path, title, summary, or tags, and fall back to unknown.

### Requirement 4: Export

**User Story:** 作为测试开发工程师，我希望导出测试设计草稿，方便继续补充、评审或提交。

#### Acceptance Criteria

1. WHEN a draft exists THEN the system SHALL provide a Markdown download action.
2. The exported file SHALL contain the same content shown in the test workbench.
3. The exported file name SHOULD be stable and easy to identify.

### Requirement 5: Evaluation and Regression Baseline

**User Story:** 作为测试开发工程师，我希望使用固定测试集评估检索和生成质量，避免每次修改都只凭感觉判断效果。

#### Acceptance Criteria

1. The system SHALL keep compatibility with the existing evaluation panel and custom evaluator.
2. The system SHALL support Golden Test Set style regression for retrieval quality.
3. The system SHOULD track Hit Rate, MRR, and faithfulness-style indicators where data is available.
4. WHEN evaluation data is missing THEN the system SHALL provide a clear setup or empty-state message.
5. Future generated test-case quality metrics SHALL be added without breaking existing RAG evaluation tests.
6. The platform SHALL provide a deterministic Golden Test Set for requirement-to-test-design evaluation.
7. The test-design evaluator SHALL compute requirement coverage, dimension coverage, citation coverage, and non-empty output metrics.
8. WHEN a test-design evaluation report is written THEN it SHALL be written under `data/evaluation/` only after an explicit CLI output argument.
9. Generated test-design evaluation reports SHALL remain ignored by default unless promoted into committed fixtures.
10. The dashboard SHALL provide a test-design evaluation page that displays aggregate metrics and per-case results.
11. The dashboard SHALL provide a deterministic test-design review page that checks missing dimensions, vague descriptions, untestable assertions, weak assertions, and missing evidence.
12. The test-design review result SHALL include score, risk level, covered dimensions, missing dimensions, and actionable findings.

### Requirement 6: Observability

**User Story:** 作为测试开发工程师，我希望能查看入库、检索、评估和后续执行链路的日志，便于定位平台输出不稳定的问题。

#### Acceptance Criteria

1. The system SHALL preserve the existing ingestion trace and query trace pages.
2. Test workbench retrieval failures SHALL surface user-readable warnings.
3. The system SHOULD later record generation input, retrieval query, retrieved snippets, and generation output as trace events.
4. Trace logging SHALL avoid storing plaintext secrets.

### Requirement 7: Test Execution Reporting

**User Story:** 作为测试开发工程师，我希望平台能查看自动化执行结果摘要、失败情况和 Allure 工件状态，便于判断本次回归质量。

#### Acceptance Criteria

1. WHEN the user opens the test reports page THEN the system SHALL show a test execution reporting view in the dashboard.
2. WHEN a valid JUnit XML file is provided THEN the system SHALL parse and display total, passed, failed, skipped, errors, and duration.
3. WHEN common Allure result or report directories exist THEN the system SHALL show their detected paths and status.
4. IF no local report artifacts exist THEN the system SHALL show a clear empty-state message and example commands for generating reports.
5. The reporting page SHALL NOT claim to execute tests by itself before an execution adapter is implemented.
6. The platform SHALL convert execution adapter results into JUnit XML when explicitly requested.
7. The test reports page SHALL discover execution-plan JUnit XML outputs from the default report directory.
8. The platform SHALL convert execution adapter results into minimal Allure results when explicitly requested.
9. The test reports page SHALL discover execution-plan Allure result outputs from the default report directory.
10. The platform SHALL save execution history records when explicitly requested by the dashboard or CLI.
11. Execution history records SHALL include scenario, adapter, status, step counts, failure reason, artifacts, and report paths.
12. The dashboard SHALL provide an execution history page that lists recent saved records and aggregate status counts.
13. The execution history page SHALL display quality trends including pass rate, failure rate, dry-run rate, daily status counts, adapter distribution, and top failure reasons.

### Requirement 8: Built-in Demo Automation Scenarios

**User Story:** 作为测试开发工程师，我希望平台内置多个代表性自动化场景，便于演示平台并验证执行与报告链路不是只支持单一示例。

#### Acceptance Criteria

1. The platform SHALL define more than one built-in demo automation scenario.
2. The platform SHALL include at least one API scenario and at least one UI smoke scenario.
3. The platform SHALL provide a stable command to run one scenario or all built-in scenarios.
4. Built-in scenarios SHALL run against deterministic local fixtures or equivalent stable targets.
5. Built-in scenarios SHALL produce report artifacts compatible with the test reporting page.

### Requirement 9: Automation Execution Planning

**User Story:** 作为测试开发工程师，我希望后续可以把自然语言测试步骤转换为自动化执行计划，并逐步接入 Playwright 或 MCP browser execution.

#### Acceptance Criteria

1. The platform SHALL provide an execution-plan preview for natural-language test steps.
2. The execution-plan preview SHALL parse supported steps into structured actions.
3. Unsupported steps SHALL be surfaced as warnings instead of silently discarded.
4. The planning page SHALL remain separate from real browser execution until a browser adapter is implemented.
5. The first execution adapter SHALL support API HTTP plans before browser UI execution.
6. WHEN dry-run mode is enabled THEN the adapter SHALL produce step results without sending network requests.
7. WHEN API execution is enabled THEN the adapter SHALL send supported API requests to a user-provided base URL and capture HTTP status and response preview.
8. Execution results SHALL include status, step logs, artifacts field, and failure reason where available.
9. Future browser execution results SHOULD include screenshots or equivalent UI artifacts.
10. The browser adapter SHALL support UI execution-plan dry-run without requiring Playwright to be installed.
11. WHEN Playwright is available THEN the browser adapter SHOULD execute supported open, input, click, submit, upload, wait, and assert-text UI actions.
12. WHEN a browser step fails THEN the browser adapter SHOULD capture a failure screenshot artifact where possible.

### Requirement 10: Safety and Repository Hygiene

**User Story:** 作为项目维护者，我希望提交到 GitHub 的代码不包含本地密钥、临时数据、旧实验输出或与当前阶段无关的目录。

#### Acceptance Criteria

1. The system repository SHALL NOT commit plaintext API keys.
2. Stage commits SHALL include only files relevant to the current stage.
3. Local experimental outputs SHALL remain untracked unless explicitly promoted into the project.
4. Each stage SHALL include a short commit message and a development log entry.

### Requirement 11: Continuous Integration

**User Story:** As a test-development engineer, I want every GitHub push or pull request to run the platform's core regression suite automatically, so reviewers can trust that the automation platform still works.

#### Acceptance Criteria

1. The repository SHALL provide a GitHub Actions workflow for pushes and pull requests targeting `main`.
2. The workflow SHALL install project runtime and dev dependencies in a clean Python environment.
3. The workflow SHALL run the core regression suite used by the staged local verification.
4. The workflow SHALL generate a JUnit XML report under `reports/`.
5. The workflow SHALL generate execution-plan dry-run report artifacts under `reports/`.
6. The workflow SHALL upload `reports/` as a CI artifact even when tests fail.
7. The workflow SHALL NOT require plaintext secrets for the default regression path.

### Requirement 12: Traceability Matrix

**User Story:** As a test-development engineer, I want to trace each requirement item to generated test points, automation scenarios, and latest execution status, so I can explain coverage and gaps during review or interviews.

#### Acceptance Criteria

1. The dashboard SHALL provide a traceability matrix page.
2. The traceability service SHALL extract requirement items from lines, bullets, or short sentence separators.
3. The traceability service SHALL extract test points from the generated Markdown test-design section and preserve testing dimensions.
4. The matrix SHALL link requirements to matching test points through deterministic keyword overlap.
5. The matrix SHALL link requirements to built-in automation scenarios where domain keywords match.
6. The matrix SHALL use execution history records to show the latest status for matched automation scenarios.
7. The matrix SHALL surface gaps such as missing test design, missing automation, automation not run, dry-run only, and latest execution failed.
8. The matrix SHALL provide table-friendly rows and JSON output for interview demos and later export.
9. The matrix SHALL support per-requirement review statuses such as unreviewed, confirmed, needs test design, needs automation, and blocked.
10. The matrix SHALL export Markdown for review discussion and CSV for spreadsheet-style analysis.

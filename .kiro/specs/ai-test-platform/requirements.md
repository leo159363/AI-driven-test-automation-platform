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

### Requirement 6: Observability

**User Story:** 作为测试开发工程师，我希望能查看入库、检索、评估和后续执行链路的日志，便于定位平台输出不稳定的问题。

#### Acceptance Criteria

1. The system SHALL preserve the existing ingestion trace and query trace pages.
2. Test workbench retrieval failures SHALL surface user-readable warnings.
3. The system SHOULD later record generation input, retrieval query, retrieved snippets, and generation output as trace events.
4. Trace logging SHALL avoid storing plaintext secrets.

### Requirement 7: Automation Execution Planning

**User Story:** 作为测试开发工程师，我希望后续可以把自然语言测试步骤转换为自动化执行计划，并逐步接入 Playwright 或 MCP browser execution.

#### Acceptance Criteria

1. Stage 1 and Stage 2 SHALL NOT pretend to execute real browser automation.
2. The design SHALL reserve a module boundary for natural-language step parsing.
3. The design SHALL reserve a module boundary for execution adapters such as Playwright or MCP browser tools.
4. Future execution results SHOULD include status, step logs, screenshots or artifacts, and failure reason.

### Requirement 8: Safety and Repository Hygiene

**User Story:** 作为项目维护者，我希望提交到 GitHub 的代码不包含本地密钥、临时数据、旧实验输出或与当前阶段无关的目录。

#### Acceptance Criteria

1. The system repository SHALL NOT commit plaintext API keys.
2. Stage commits SHALL include only files relevant to the current stage.
3. Local experimental outputs SHALL remain untracked unless explicitly promoted into the project.
4. Each stage SHALL include a short commit message and a development log entry.

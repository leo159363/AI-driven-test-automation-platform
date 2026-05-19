# AI 驱动的自动化测试平台

[![CI](https://github.com/leo159363/AI-driven-test-automation-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/leo159363/AI-driven-test-automation-platform/actions/workflows/ci.yml)

面向测试开发岗位的 AI 自动化测试平台原型。项目基于原有 Modular RAG MCP Server 改造，保留 RAG、MCP、Streamlit Dashboard、pytest、评估和可观测能力，并把产品定位收敛到测试开发常见工作流：

```text
需求/接口/缺陷/规范
  -> 测试知识库检索
  -> 测试点草稿生成
  -> 测试设计质量评估
  -> 自动化场景执行
  -> JUnit / Allure 报告查看
  -> 自然语言执行计划与 API / UI 执行适配
```

这个项目不是完整的企业级 TestOps SaaS，而是一个适合面试讲解的工程化闭环：能说明测试设计、RAG 检索、自动化执行、报告分析、质量评估和 MCP 工具化扩展如何组合在一起。

## 当前能力

| 模块 | 能力 | 关键文件 |
| --- | --- | --- |
| 测试工作台 | 输入需求，按功能、边界、异常、安全、并发、回归维度生成测试点草稿，并可导出 Markdown | `src/observability/dashboard/pages/test_workbench.py` |
| 知识源分类 | 将检索片段归类为需求文档、API 文档、缺陷记录、测试规范、执行日志或未知来源 | `src/observability/dashboard/services/test_design_service.py` |
| 测试设计评估 | 使用 Golden Test Set 评估需求覆盖率、维度覆盖率、引用覆盖率和空输出，支持 CLI 与 Dashboard 展示 | `src/observability/dashboard/pages/test_design_evaluation.py` |
| 自动化场景 | 内置 API 登录、API 文件上传、UI 登录冒烟场景，可生成 JUnit XML，并兼容 Allure 结果目录 | `scripts/run_automation_suite.py` |
| 测试报告中心 | 解析 pytest JUnit XML，发现 Allure 结果目录和 HTML 报告目录 | `src/observability/dashboard/pages/test_reports.py` |
| 执行计划 | 将自然语言步骤解析为结构化执行计划，识别 API 与 UI 计划 | `src/observability/dashboard/services/execution_plan_service.py` |
| API 执行适配器 | 支持 API 计划 dry-run 和真实 HTTP 执行，返回步骤状态、日志、失败原因、响应预览，并可导出 JUnit XML / Allure results | `src/observability/dashboard/services/api_execution_adapter.py` |
| Browser UI 执行适配器 | 支持 UI 计划 dry-run、可选 Playwright 真执行、失败截图和统一报告导出 | `src/observability/dashboard/services/browser_execution_adapter.py` |
| 执行历史 | 保存 API / UI 执行计划记录，展示状态、失败原因、报告路径、截图 artifact、通过率和失败原因分布 | `src/observability/dashboard/pages/execution_history.py` |
| RAG / MCP 基座 | 保留文档入库、Hybrid Search、MCP tools、摄取追踪、查询追踪和评估面板 | `src/` |

## 技术栈

- Python 3.10+
- Streamlit Dashboard
- pytest / JUnit XML / optional Allure / optional Playwright
- RAG ingestion pipeline
- Dense retrieval + BM25 sparse retrieval + RRF fusion + optional rerank
- ChromaDB vector store
- MCP Server tools
- Deterministic Golden Test Set evaluation

## 快速开始

### 1. 安装依赖

如果仓库里已经有 `.venv`，可以直接使用。全新环境可执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### 2. 启动 Dashboard

```powershell
.\.venv\Scripts\python.exe scripts\start_dashboard.py --port 8501
```

打开 `http://localhost:8501` 后，建议按这个顺序演示：

1. `测试工作台`：输入一段需求，生成测试点草稿。
2. `自动化场景`：查看内置 API / UI 自动化示例。
3. `执行计划`：选择 API 登录或 UI 登录场景，生成自然语言步骤对应的执行计划，可开启 dry-run。
4. `执行历史`：查看保存过的执行计划记录、通过率趋势、状态分布、失败原因和报告路径。
5. `测试报告`：查看 JUnit XML 和 Allure 目录状态。
6. `测试设计评估`：运行 Golden Test Set，展示测试点生成质量指标。
7. `评估中心`：说明已有 RAG 评估入口。

### 3. 运行内置自动化场景

```powershell
.\.venv\Scripts\python.exe scripts\run_automation_suite.py --scenario all --disable-allure
```

默认输出：

- `reports/junit.xml`
- `reports/allure-results/`，仅在安装 `allure-pytest` 且未禁用时生成

### 4. 运行测试设计评估

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_test_design.py
```

如需显式生成 JSON 报告：

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_test_design.py --output data/evaluation/test_design_report.json
```

`data/` 已在 `.gitignore` 中忽略，生成报告默认不会进入 Git 提交。

### 5. 运行执行计划并生成 JUnit XML / Allure Results

```powershell
.\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario api_login --dry-run --junitxml reports\execution-plan-junit.xml
.\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario ui_login_smoke --adapter browser --dry-run --junitxml reports\execution-plan-junit.xml --allure-results reports\execution-plan-allure-results --record-history
```

生成后可以在 Dashboard 的 `测试报告` 页面查看该 JUnit XML 汇总。

Browser UI 真执行需要额外安装 Playwright 浏览器依赖；dry-run 不需要：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[browser]"
.\.venv\Scripts\python.exe -m playwright install chromium
```

### 6. 运行核心回归测试

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_browser_execution_adapter.py tests\unit\test_execution_result_report_service.py tests\unit\test_execution_history_service.py tests\unit\test_run_execution_plan_script.py tests\unit\test_test_design_evaluation_service.py tests\unit\test_test_design_service.py tests\unit\test_api_execution_adapter.py tests\unit\test_execution_plan_service.py tests\automation tests\unit\test_automation_scenario_service.py tests\unit\test_test_report_service.py tests\unit\test_dashboard_config.py tests\e2e\test_dashboard_smoke.py tests\e2e\test_mcp_client.py::TestMCPClientE2E::test_initialize_and_tools_list -v
```

最近一次阶段回归结果：`80 passed`。

### 7. GitHub Actions CI

仓库已接入 GitHub Actions。每次 push 或 pull request 到 `main` 时会自动安装依赖、运行核心回归测试、生成 `reports/ci-junit.xml`，并上传 `reports/` 作为 CI artifact。

## Spec 与阶段记录

项目按阶段推进，规格文档位于：

- `.kiro/specs/ai-test-platform/requirements.md`
- `.kiro/specs/ai-test-platform/design.md`
- `.kiro/specs/ai-test-platform/tasks.md`
- `docs/development_log.md`

已完成阶段：

| Stage | 内容 |
| --- | --- |
| Stage 1 | 项目定位为 AI 驱动的自动化测试平台 |
| Stage 2 | 建立需求、设计、任务规格文档 |
| Stage 3 | 抽取测试设计服务并增加单元测试 |
| Stage 4 | 增加测试报告中心 |
| Stage 5 | 增加内置自动化场景和统一 runner |
| Stage 6 | 增加知识源分类 |
| Stage 7 | 增加测试设计 Golden Test Set 评估 |
| Stage 8 | 增加自然语言执行计划预览 |
| Stage 9 | 增加 API 执行适配器 |
| Stage 10 | 整理 README 和面试交付文档 |
| Stage 11 | 增加执行结果 JUnit XML 导出 |
| Stage 12 | 增加测试设计评估 Dashboard 页面 |
| Stage 13 | 增加 Browser UI 执行适配器和 Allure 结果导出 |
| Stage 14 | 增加 GitHub Actions CI 和报告 artifact |
| Stage 15 | 增加执行历史和测试任务记录 |
| Stage 16 | 增加执行质量趋势和失败原因分析 |

## 面试讲法

可以用下面这段作为 1 分钟介绍：

> 我这个项目是一个面向测试开发场景的 AI 自动化测试平台。它不是只做一个页面 demo，而是把需求输入、RAG 知识检索、测试点生成、质量评估、自动化场景执行、执行历史、测试报告展示和执行计划适配串成一个闭环。核心思路是：测试人员输入需求或接口说明后，系统结合需求文档、API 文档、缺陷记录、测试规范和执行日志生成结构化测试点；再用 Golden Test Set 评估生成质量；自动化侧内置 API 和 UI 场景，能输出 JUnit / Allure 兼容报告；最后通过自然语言执行计划接入 API HTTP adapter 和 Browser UI adapter，展示从“生成计划”到“执行记录和报告中心”的路径。

重点可以讲 5 个技术点：

1. **RAG 增强测试设计**：不是凭模板生成，而是支持从历史缺陷、API 文档、测试规范里召回证据。
2. **知识源分类**：把检索结果按需求、API、缺陷、规范、执行日志分类，便于测试人员判断依据来源。
3. **质量评估闭环**：用 Golden Test Set 在 Dashboard 中展示覆盖率、引用质量和空输出，避免只凭感觉判断 AI 输出。
4. **自动化与报告链路**：pytest 场景可稳定运行，并输出 JUnit XML，Dashboard 能展示报告状态，GitHub Actions 能在每次提交后自动回归并上传报告产物。
5. **执行适配器边界**：API HTTP adapter 和 Browser UI adapter 都复用同一套 ExecutionPlan / ExecutionResult 模型，避免把规划逻辑和执行逻辑耦合，并将执行结果保存为历史记录、导出为 JUnit XML / Allure results 供报告中心复用，同时在执行历史中展示质量趋势。

更完整的面试讲解见 [docs/interview_guide.md](docs/interview_guide.md)。

## 仓库卫生

- 不提交本地 API key、`config/settings.yaml` 备份、向量库、缓存、日志、报告和实验导出。
- `data/`、`logs/`、`reports/`、`allure-results/`、`allure-report/` 默认被忽略。
- 每个阶段只提交与当前目标相关的文件，避免混入无关业务项目或历史实验目录。

## 下一步可扩展方向

- 接入 MCP browser 工具或真实业务测试站点，补齐更复杂 UI 操作。
- 增加测试设计评估趋势，把 Golden Test Set 得分也纳入质量看板。
- 给测试设计评估增加重复测试点、不可执行断言、风险覆盖等指标。
- 给知识检索增加 source type 过滤器。
- 增加 Docker / CI，使自动化场景和评估在 GitHub Actions 中运行。

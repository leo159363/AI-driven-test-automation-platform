# QualityPilot

[![CI](https://github.com/leo159363/AI-driven-test-automation-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/leo159363/AI-driven-test-automation-platform/actions/workflows/ci.yml)

QualityPilot 是一个基于 **MCP + RAG** 的智能自动化测试平台，面向测试开发场景，支持测试知识检索、测试用例生成、API 自动化执行、JUnit/Allure 报告解析、失败原因分析和 Bug 报告生成。

项目定位不是完整企业级 TestOps 系统，而是一个适合测试开发实习面试讲解的工程化闭环：

```text
文档 / RAG 上下文
  -> 测试用例生成
  -> API 自动化执行
  -> JUnit / Allure 报告解析
  -> 失败用例查询
  -> 失败原因分析
  -> Bug 报告草稿生成
```

## 1. 一条命令运行 Demo

```powershell
.\.venv\Scripts\python.exe scripts\run_qualitypilot_demo.py
```

Demo 会启动一个本地登录接口 stub，真实执行 API 自动化场景，并故意制造一个稳定失败：接口返回 HTTP 200，但缺少需求要求的 `token` 字段。随后平台会解析报告、定位失败用例、分析原因，并生成 Bug 草稿。

运行成功后会看到类似输出：

```text
QualityPilot demo completed
execution_status=failed
report_status=failed
failed_case_count=1
bug_count=1
junitxml=reports/qualitypilot-demo/junit.xml
allure_results=reports/qualitypilot-demo/allure-results
summary_json=reports/qualitypilot-demo/demo_summary.json
bug_report_md=reports/qualitypilot-demo/bug_report.md
```

面试时建议重点展示：

- `reports/qualitypilot-demo/junit.xml`：标准 JUnit XML 测试报告。
- `reports/qualitypilot-demo/demo_summary.json`：完整链路结构化输出。
- `reports/qualitypilot-demo/bug_report.md`：可复制到缺陷平台的 Bug 草稿。

更详细的演示说明见 [docs/qualitypilot_demo.md](docs/qualitypilot_demo.md)。

## 2. 核心能力

| 模块 | 已实现能力 | 体现的测试开发能力 |
| --- | --- | --- |
| RAG 测试上下文 | 支持需求、接口文档、历史 Bug、测试报告、日志等 source type 元数据 | 测试设计需要证据来源，不是凭空生成 |
| MCP Server | 将测试开发动作封装为可编排 tools | 面向 Agent / IDE / 自动化工作流扩展 |
| 测试用例生成 | 根据需求和 RAG 上下文生成结构化测试用例 | 功能、异常、安全、回归等维度覆盖 |
| API 自动化执行 | 执行 API 场景，输出 step 级结果 | pytest / HTTP adapter / 执行计划落地 |
| 测试报告解析 | 解析 JUnit XML，发现 Allure results | 自动化测试平台必须能消费报告 |
| 失败用例查询 | 按状态、关键字、类名、用例名筛选失败用例 | 支持失败定位和回归分析 |
| 失败原因分析 | 输出可能根因、置信度、证据、建议修复 | 从“跑失败”推进到“分析失败” |
| Bug 报告生成 | 生成结构化缺陷草稿和 Markdown | 打通测试执行到缺陷提交前的最后一步 |
| Dashboard | 保留 Streamlit 页面、测试报告、执行历史、追踪矩阵等能力 | 展示平台化思路，而不是脚本集合 |

## 3. MCP Tools

当前核心 tools：

| Tool | 用途 |
| --- | --- |
| `retrieve_test_context` | 检索测试设计、失败分析、Bug 生成所需上下文 |
| `generate_test_cases` | 从需求和上下文生成结构化测试用例 |
| `run_api_tests` | 执行 API 自动化场景并生成报告路径 |
| `get_test_report` | 解析 JUnit/Allure 测试报告 |
| `query_failed_cases` | 查询失败、错误、跳过用例 |
| `analyze_failure` | 分析失败原因并给出修复建议 |
| `generate_bug_report` | 生成结构化 Bug 草稿和 Markdown |

保留的基础知识库 tools：

```text
query_knowledge_hub
list_collections
get_document_summary
```

完整参数和输出示例见 [docs/mcp_tools.md](docs/mcp_tools.md)。

## 4. 技术栈

- Python 3.10+
- MCP Server
- RAG ingestion pipeline
- ChromaDB / BM25 / hybrid retrieval
- pytest
- JUnit XML
- Allure-compatible results
- Streamlit Dashboard
- GitHub Actions CI

## 5. 快速开始

安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

启动 MCP Server：

```powershell
.\.venv\Scripts\mcp-server.exe
```

或：

```powershell
.\.venv\Scripts\python.exe -m src.mcp_server.server
```

启动 Dashboard：

```powershell
.\.venv\Scripts\python.exe scripts\start_dashboard.py --port 8501
```

运行核心 Demo：

```powershell
.\.venv\Scripts\python.exe scripts\run_qualitypilot_demo.py
```

运行相关测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_qualitypilot_demo_script.py tests\unit\test_generate_bug_report_tool.py tests\unit\test_analyze_failure_tool.py tests\unit\test_run_api_tests_tool.py -v
```

## 6. 项目结构

```text
src/
  mcp_server/
    tools/                  # MCP tools：检索、用例生成、执行、报告、失败分析、Bug 生成
  ingestion/                # 文档入库、切分、向量化、存储
  core/                     # RAG 查询、检索、响应组装
  observability/dashboard/  # Streamlit Dashboard 与测试平台页面
scripts/
  run_qualitypilot_demo.py  # 端到端面试 Demo
  run_automation_suite.py   # 内置自动化场景 runner
  run_execution_plan.py     # 自然语言执行计划 runner
docs/
  qualitypilot_demo.md      # 面试 Demo 说明
  mcp_tools.md              # MCP tools 文档
  interview_guide.md        # 面试讲解指南
tests/
  unit/                     # 核心单元测试
  integration/              # MCP / 服务集成测试
  e2e/                      # 端到端协议测试
```

## 7. 面试讲法

可以这样介绍：

> QualityPilot 是一个面向测试开发场景的 MCP + RAG 智能自动化测试平台。我把测试开发常见链路拆成多个 MCP tools：先检索需求和接口文档上下文，再生成测试用例，然后执行 API 自动化测试，生成 JUnit / Allure 报告。报告失败后，平台会查询失败用例，结合上下文分析失败原因，并生成结构化 Bug 草稿。项目重点不是做一个大而全的企业系统，而是把“测试设计、自动化执行、报告解析、失败分析、缺陷草稿”这条闭环做清楚、跑得通、能测试。

简历可写：

```text
基于 Python、MCP、RAG、pytest、JUnit XML 和 Streamlit 实现智能自动化测试平台，封装测试上下文检索、用例生成、API 自动化执行、报告解析、失败用例查询、失败原因分析和 Bug 草稿生成等 MCP tools，并提供稳定端到端 Demo，打通从需求到缺陷报告的测试开发闭环。
```

## 8. 当前边界

- 当前不是完整企业级 TestOps 平台，没有复杂权限、任务调度、多环境管理和外部缺陷系统写入。
- 失败分析和 Bug 生成目前以规则兜底为主，保证本地和 CI 稳定；后续可以接入 LLM 做总结增强。
- Allure 当前生成 compatible results，未强依赖本机安装 Allure CLI 生成 HTML。
- Demo 使用本地 stub 服务制造稳定失败，便于面试现场复现。

## 9. 后续路线

优先级建议：

1. 增加完整端到端 MCP tools/call 测试，验证每个 tool 的协议输入输出。
2. 增加 Allure HTML 生成说明或可选脚本。
3. 增加 Dashboard 中的“AI 测试闭环 Demo”页面，把当前 CLI Demo 可视化。
4. 将失败分析结果和 Bug 草稿保存到本地历史记录。
5. 接入真实业务 Demo API 或公开测试站点，替换部分 stub 场景。

# QualityPilot 面试前检查清单

这份清单用于面试前快速复盘，目标是把项目讲成一个“测试开发闭环”，而不是零散脚本或单纯 AI 生成文本。

## 1. 30 秒定位

QualityPilot 是一个基于 MCP + RAG 的智能自动化测试平台，面向测试开发场景，支持测试知识检索、测试用例生成、自动化执行、报告解析、失败分析和 Bug 报告生成。

一句话重点：

```text
我把测试开发从需求理解到缺陷草稿的链路拆成 MCP tools，并用 RAG 给用例生成和失败分析提供上下文证据。
```

## 2. 3 分钟项目讲法

推荐顺序：

1. 先讲项目为什么做：测试开发不仅要写脚本，还要覆盖需求分析、用例设计、执行、报告、失败定位和缺陷提交。
2. 再讲技术架构：Python + MCP Server + RAG + pytest + JUnit XML + Allure + Streamlit Dashboard + GitHub Actions。
3. 再讲核心闭环：文档/RAG 上下文 -> 测试用例生成 -> API 自动化执行 -> JUnit/Allure 报告解析 -> 失败查询 -> 失败分析 -> Bug 草稿。
4. 最后讲工程化：有单元测试、E2E MCP tools/call 测试、Dashboard smoke test、CI artifact 和面试 Demo。

## 3. 10 分钟演示流程

本地演示推荐按这个顺序：

1. 运行端到端 Demo：

```powershell
.\.venv\Scripts\python.exe scripts\run_qualitypilot_demo.py
```

2. 打开输出：

```text
reports/qualitypilot-demo/demo_summary.json
reports/qualitypilot-demo/junit.xml
reports/qualitypilot-demo/bug_report.md
reports/qualitypilot-demo/allure-results/
```

3. 如果本机有 Allure commandline，生成 HTML：

```powershell
.\.venv\Scripts\python.exe scripts\generate_allure_report.py
```

4. 启动 Dashboard：

```powershell
.\.venv\Scripts\python.exe scripts\start_dashboard.py --port 8501
```

5. 进入 `QualityPilot Demo` 页面，按页面从上到下讲 MCP workflow、RAG contexts、测试用例、失败用例、失败分析和 Bug 草稿。

6. 打开 GitHub Actions，说明 CI 会上传：

```text
ai-test-platform-reports
allure-html-report
```

## 4. 必须讲清楚的已实现能力

- MCP tools：`retrieve_test_context`、`generate_test_cases`、`run_api_tests`、`get_test_report`、`query_failed_cases`、`analyze_failure`、`generate_bug_report`。
- RAG 元数据：`project`、`module`、`version`、`source_type`、`source_id`。
- 自动化执行：API 登录、文件上传、UI 登录 dry-run，以及自然语言执行计划。
- 报告能力：JUnit XML 解析、Allure results、Allure HTML 生成脚本、CI HTML artifact。
- Dashboard：QualityPilot Demo、测试报告、执行历史、追踪矩阵、测试设计评审、测试设计评估。
- CI：push/PR 后自动跑核心回归并上传报告。

## 5. 不要夸大的边界

- 不要说这是完整企业级 TestOps 平台，当前没有复杂权限、任务调度、多环境管理和缺陷系统写入。
- 不要说失败分析完全依赖大模型，当前主要是规则兜底，后续可以接 LLM 总结增强。
- 不要说已经接入 Allure 服务端，当前是 Allure results + 静态 HTML artifact。
- 不要说 UI 场景一定真实打开浏览器，默认 dry-run 稳定演示，真实 Playwright 执行需要环境准备。
- 不要说 RAG 在大规模真实业务知识库验证过，当前更适合作为面试项目和可扩展原型。

## 6. 高频追问回答

### 和普通 pytest 框架有什么区别？

普通 pytest 主要解决执行问题。QualityPilot 把执行前后的测试开发动作也串起来：RAG 检索、用例生成、执行、报告解析、失败分析和 Bug 草稿生成。

### 为什么要用 MCP？

MCP 把测试开发动作封装成标准工具，让 IDE、Agent 或其他客户端可以按协议调用，而不是只能手工运行某个脚本。

### 为什么要用 RAG？

测试用例和失败分析需要需求、接口文档、历史 Bug、测试报告和日志作为证据。RAG 用来召回这些上下文，减少凭空生成。

### Allure 做到什么程度？

项目能生成 Allure-compatible results，也提供 `scripts/generate_allure_report.py` 生成静态 HTML。CI 中会安装 Allure commandline 并上传 `allure-html-report` artifact。

### 发现过什么问题？

可以回答：开发过程中通过自动化测试发现过报告状态映射、Dashboard 页面导入、CLI 参数兼容和 Allure result 生成路径问题，修复后都加入了回归测试。

## 7. 简历写法精简版

```text
QualityPilot 智能自动化测试平台
- 基于 Python、MCP、RAG、pytest、JUnit XML、Allure 和 Streamlit 构建测试开发工作台，打通测试知识检索、用例生成、自动化执行、报告解析、失败分析和 Bug 草稿生成闭环。
- 设计并实现 retrieve_test_context、generate_test_cases、run_api_tests、get_test_report、query_failed_cases、analyze_failure、generate_bug_report 等 MCP tools，输出结构化 JSON，支持 Agent 编排。
- 内置 API 登录、文件上传和 UI 登录 dry-run 自动化场景，支持 JUnit XML、Allure results、Allure HTML artifact 和 GitHub Actions CI 报告上传。
- 提供 Dashboard 展示端到端 Demo、执行历史、测试报告、追踪矩阵、测试设计评审和 Golden Test Set 评估，提升项目可演示性和测试闭环可追溯性。
```

## 8. 下一步优先级

1. 将失败分析结果和 Bug 草稿保存进执行历史，形成可追溯缺陷分析记录。
2. 接入一个真实 Demo API 或公开测试站点，减少 stub 场景比例。
3. 增加轻量性能基线，优先覆盖 RAG 检索、报告解析和执行历史聚合。
4. 后续再考虑 LLM 总结增强、GitHub Issues 写入或外部缺陷系统集成。

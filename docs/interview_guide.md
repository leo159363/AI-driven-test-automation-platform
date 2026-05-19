# Interview Guide

本文档用于准备测试开发岗位面试，重点说明这个项目应该怎么讲、怎么演示，以及面试官追问时如何回答。

## 1 分钟项目介绍

这是一个面向测试开发场景的 AI 驱动自动化测试平台。项目基于 RAG 和 MCP 架构改造，核心闭环是：输入需求或接口说明，系统结合需求文档、API 文档、缺陷记录、测试规范和执行日志生成测试点草稿；再用 Golden Test Set 评估生成质量；自动化侧内置 API 和 UI 场景，能输出 JUnit / Allure 兼容报告；执行层支持自然语言步骤解析，并接入 API HTTP adapter 与 Browser UI adapter。

## 推荐演示顺序

1. 打开 Dashboard：

```powershell
.\.venv\Scripts\python.exe scripts\start_dashboard.py --port 8501
```

2. 进入 `测试工作台`，输入一段需求，例如：

```text
登录接口需要支持用户名密码认证，连续五次失败后临时锁定账户，并且错误提示不能泄露账号是否存在。
```

选择 `接口测试设计`，关注 `功能 / 异常 / 安全 / 回归`，生成测试点草稿。

3. 进入 `自动化场景`，说明平台内置了 API 登录、API 文件上传、UI 登录冒烟，不是只支持单一 demo。

4. 运行自动化场景：

```powershell
.\.venv\Scripts\python.exe scripts\run_automation_suite.py --scenario all --disable-allure
```

5. 进入 `测试报告`，查看 `reports/junit.xml` 的汇总。

6. 进入 `执行计划`，选择 API 登录场景或 UI 登录冒烟场景，生成计划，说明自然语言步骤会变成结构化 action。

7. 执行计划也可以导出成 JUnit XML：

```powershell
.\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario api_login --dry-run --junitxml reports\execution-plan-junit.xml
.\.venv\Scripts\python.exe scripts\run_execution_plan.py --scenario ui_login_smoke --adapter browser --dry-run --junitxml reports\execution-plan-junit.xml --allure-results reports\execution-plan-allure-results
```

8. 进入 `测试设计评估`，点击运行 Golden Test Set，展示需求覆盖率、维度覆盖率、引用覆盖率和空输出指标。也可以用 CLI 运行：

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_test_design.py
```

说明这个项目不是只看 AI 输出好不好，而是用固定样例做质量回归，并且评估结果可以直接在 Dashboard 中展示。

## 可以重点讲的设计

### RAG 为什么适合测试设计

测试设计依赖大量上下文：需求、接口约束、历史缺陷、测试规范、执行失败记录。单纯模板生成容易漏掉历史风险点。RAG 可以把这些资料作为证据召回，生成测试点时带上依据，测试人员可以复核来源。

### 为什么要做知识源分类

同样是一个检索片段，来自需求、API 文档、缺陷记录、测试规范和执行日志的可信度和用途不同。项目里把来源类型标准化，页面和 Markdown 草稿都会展示来源类型，方便判断这是规则依据、历史风险还是执行反馈。

### 为什么要做 Golden Test Set

AI 生成质量不能只靠肉眼感觉。项目用固定需求样例评估：

- requirement coverage：期望关键词是否覆盖；
- dimension coverage：功能、边界、异常、安全、回归等维度是否覆盖；
- citation coverage：应该引用的证据是否出现；
- non-empty output：是否出现空输出。

这些指标虽然简单，但足够作为第一版回归基线。项目现在同时提供 CLI 和 Dashboard 页面，便于本地回归和面试演示。

### 为什么 Browser adapter 默认先用 dry-run

真实 UI 执行依赖浏览器安装、页面环境和选择器稳定性，面试演示时不应该把核心链路绑死在本机浏览器环境上。所以项目把 Browser adapter 做成两层：dry-run 可稳定展示自然语言步骤到执行结果的链路；安装 Playwright 后可以进入真实浏览器执行，并在失败时输出截图路径。这样既能讲架构，也能避免 demo 不稳定。

### 报告中心的价值

测试开发不只是写脚本，还要看执行质量。项目的报告中心能解析 JUnit XML，并发现 Allure 目录。自动化场景和执行计划 adapter 都可以产生 JUnit XML；执行计划结果还能生成最小 Allure results，这样可以把自动化执行、自然语言执行计划和测试报告展示串起来，面试时能讲完整链路。

## 高频追问与回答

### 这个项目和普通自动化测试框架有什么区别？

普通框架侧重执行脚本，这个项目把测试设计也纳入平台：需求输入、知识检索、测试点生成、质量评估、自动化执行和报告查看都在一个闭环里。它更像智能测试工作台，而不只是 pytest 脚本集合。

### RAG 部分怎么落到测试开发？

把 PRD、接口文档、历史缺陷、测试规范、执行日志入库。生成测试点时，先检索相关资料，再把证据片段附加到测试设计草稿中。比如登录需求会召回认证 API 文档、历史锁定缺陷和错误码规范，从而补充安全、异常和回归测试点。

### 怎么证明 AI 生成结果可靠？

第一版用 deterministic Golden Test Set 做回归，指标包括需求覆盖、维度覆盖、引用覆盖和空输出。未来可以继续加重复率、不可执行断言、风险覆盖、人工评审通过率等指标。

### 为什么当前不是完整企业级平台？

这是面试导向的工程原型，目标是讲清楚核心技术闭环。企业级平台还需要用户权限、项目空间、用例管理、任务调度、CI 集成、环境管理等能力，这些不是第一版重点。

### 如果继续扩展，你会先做什么？

优先接入 CI，让自动化场景、执行计划 dry-run 和测试设计评估在 GitHub Actions 中稳定运行。下一步再接 MCP browser 工具或真实业务测试站点，扩展更复杂的 UI 交互、截图和 trace。

## 简历写法参考

可以按下面方式写，注意要结合自己的真实掌握程度调整：

```text
AI 驱动的自动化测试平台
- 基于 Python、Streamlit、pytest、RAG 和 MCP 设计测试开发工作台，串联需求输入、知识检索、测试点生成、自动化执行、报告展示与质量评估链路。
- 构建测试知识源分类能力，将需求文档、API 文档、缺陷记录、测试规范和执行日志标准化展示，提升测试设计依据可追溯性。
- 实现测试设计 Golden Test Set 评估，计算需求覆盖率、维度覆盖率、引用覆盖率和空输出指标，支持生成逻辑的稳定回归。
- 内置 API 登录、文件上传和 UI 登录冒烟自动化场景，支持 pytest 执行、JUnit XML 输出和 Allure 目录发现。
- 设计自然语言执行计划解析与 API HTTP / Browser UI adapter，支持 dry-run、真实 HTTP 执行、可选 Playwright UI 执行、步骤日志、响应预览、失败截图和失败原因记录。
- 将执行适配器结果转换为 JUnit XML / Allure results，使自然语言执行计划结果能进入统一测试报告中心展示。
```

## 不建议夸大的点

- 不要说这是完整企业级 TestOps 平台。
- 不要说 UI 真执行不需要环境准备；真实 Browser adapter 需要安装 Playwright 和浏览器依赖，dry-run 可直接演示。
- 不要说 RAG 检索质量已经在大规模业务数据上验证，当前只完成通用 fixture 和评估框架。
- 不要说自动化报告已完整集成 Allure 服务端，当前是生成/发现本地 Allure results 和报告目录。

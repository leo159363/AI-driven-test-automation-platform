# QualityPilot 面试讲解手册

## 1. 项目一句话介绍

QualityPilot 是一个基于 Vue + FastAPI + MCP + RAG + pytest + Allure 的智能自动化测试平台，面向测试开发场景，覆盖“知识检索、用例生成、自动化执行、报告解析、失败分析、Bug 报告生成”的闭环。

## 2. 30 秒介绍

我做这个项目的目的是把测试开发岗位常见能力串成一个可运行的平台，而不是只写几个自动化脚本。平台前端用 Vue，后端用 FastAPI，测试执行用 pytest，报告解析支持 JUnit / Allure。AI 部分不是简单聊天，而是先把需求、接口文档、历史 Bug、测试报告等资料放进知识库，再通过 RAG 检索作为上下文，辅助生成测试用例、分析失败原因和生成 Bug 报告。核心能力也封装成 MCP tools，方便被 Agent 或 IDE 调用。

## 3. 2 分钟讲解流程

1. 先打开 Vue 首页，说明这是测试开发平台原型。
2. 进入 API 测试中心，展示接口目录、请求样例、断言、关联测试用例和 pytest 目标。
3. 在 API 测试中心发送一次登录接口请求，展示状态码断言和 JSON 字段断言。
4. 进入测试用例页面，说明用例按接口、UI、功能、异常、安全等维度组织。
5. 进入自动化执行页面，选择场景触发后端 pytest 执行。
6. 进入测试报告页面，展示 JUnit / Allure 产物和执行摘要。
7. 进入知识库管理页面，说明需求、接口文档、历史 Bug、日志和测试报告可以作为 RAG 来源。
8. 进入 AI 测试助手，选择“智能用例生成”或“失败原因分析”模板，展示结构化输出。
9. 最后说明 MCP tools 把这些能力封装成可编排工具，可以被 Agent 调用。

## 4. 核心架构

```text
Vue 前端
  -> FastAPI API 层
    -> 测试用例 / 接口目录 / 自动化执行 / 报告 / AI 助手 / 知识库接口
      -> pytest runner
      -> JUnit / Allure report parser
      -> RAG retrieval service
      -> MCP tools
```

为什么这样设计：

- Vue 负责真实平台页面，面试观感比 Streamlit 更接近公司内部测试平台。
- FastAPI 负责把 Python 测试能力封装成 HTTP API。
- pytest 负责真正执行测试，报告用 JUnit / Allure 方便 CI 和平台解析。
- RAG 让 AI 生成结果有依据，避免“凭空生成”。
- MCP tools 让平台能力可以被 Agent、IDE、自动化工作流调用。

## 5. 功能模块怎么讲

### API 测试中心

讲法：

> 这里参考了 Postman / Apifox / 测试平台常见结构，但没有照搬。左侧是接口目录，中间是接口列表，右侧是请求调试器和接口详情。用户可以编辑 headers、request body、状态码断言和 JSON 字段断言，点击发送后查看响应体、耗时和断言结果。为了安全，真实 HTTP 调试只允许 localhost，默认使用内置 mock 目标保证 demo 稳定。

本阶段又参考了 FullScopeTest 的 API 工作台思路，补上环境变量、公共 Headers、Query Params、自定义 Mock 响应、cURL 导出、AI 用例裂变和自然语言编排预览。区别是 QualityPilot 没有照搬它的 Flask/React/Celery 实现，而是放到 Vue + FastAPI 架构里，并继续和 RAG/MCP 流程打通。

体现能力：

- API 测试建模
- 接口请求调试
- 环境变量和 `{{variable}}` 占位符替换
- Query Params / Headers / Body 统一建模
- Mock 响应和本地受控 HTTP 调试
- 状态码和 JSON 字段断言
- AI 生成正常、异常、边界、安全类接口用例
- 自然语言生成接口测试编排计划
- cURL 导出
- 测试用例和接口关联
- 测试平台页面设计
- 自动化场景可追踪

### 自动化执行

讲法：

> 前端点击运行后，FastAPI 后端调用 pytest runner 执行指定场景。执行结束后生成 JUnit XML 和 Allure-compatible results，并记录 run_id、状态、耗时、通过数、失败数和产物路径。

体现能力：

- pytest 自动化执行
- 后端任务封装
- 测试报告产物管理
- 平台触发自动化测试

### 报告解析

讲法：

> 自动化平台不能只运行测试，还要能解析结果。我这里解析 JUnit XML，同时发现 Allure results / Allure report 路径，把执行结果转成前端能展示的结构化数据。

体现能力：

- JUnit XML 报告解析
- Allure 结果管理
- 失败用例统计
- CI artifact 思路

### 知识库与 RAG

讲法：

> AI 生成测试用例时，如果没有上下文，很容易变成普通聊天。所以我把需求、接口文档、测试规范、历史 Bug、测试报告和日志都设计成 source_type，检索时可以按 project、module、version、source_type 过滤，召回片段会带 source_id 和 metadata，方便追溯。

体现能力：

- RAG 数据流理解
- 测试知识资产管理
- 元数据过滤
- 引用来源可追溯

### AI 测试助手

讲法：

> AI 助手不是一个普通聊天窗口，而是围绕测试开发任务做了提示词模板，例如智能用例生成、接口测试设计、失败原因分析、Bug 报告生成、可测性分析。它可以复用知识库检索结果，输出结构化 JSON 和 Markdown。

体现能力：

- 提示词模板设计
- RAG + LLM 任务编排
- 结构化测试产物生成
- 失败分析和缺陷报告能力

### MCP tools

讲法：

> MCP tools 是为了让平台能力不只在页面里用，也能被 Agent 或 IDE 调用。我把 retrieve_test_context、generate_test_cases、run_api_tests、get_test_report、query_failed_cases、analyze_failure、generate_bug_report 这些动作封装成工具，输入输出尽量是结构化 JSON。

体现能力：

- 工具化思维
- Agent 工作流接入
- 自动化链路编排
- 结构化接口设计

## 6. 简历写法

项目名称：

```text
QualityPilot：基于 MCP + RAG 的智能自动化测试平台
```

简历描述：

```text
基于 Vue 3 + FastAPI + pytest + MCP + RAG 实现智能自动化测试平台，支持接口测试目录、测试用例管理、pytest 自动化执行、JUnit/Allure 报告解析、RAG 知识检索、AI 用例生成、失败原因分析和 Bug 报告草稿生成。
```

项目职责：

```text
- 设计 Vue + FastAPI 全栈架构，将 Python 自动化测试能力封装为 HTTP API，支撑前端平台化操作。
- 构建 API 测试中心，维护接口 method、path、headers、request body、assertions、关联测试用例和 pytest 执行目标，并支持受控接口调试和断言结果展示。
- 实现自动化执行接口，支持前端触发 pytest 场景运行，并生成 JUnit XML 与 Allure-compatible 测试报告。
- 设计测试知识库 source_type 元数据，支持需求、接口文档、历史 Bug、测试报告、日志和规范的 RAG 检索。
- 封装 MCP tools，包括上下文检索、用例生成、API 测试执行、报告解析、失败分析和 Bug 报告生成。
- 接入 GitHub Actions，执行 ruff、pytest 和报告产物上传，形成基础 CI 流程。
```

技术亮点：

```text
Vue 3 / FastAPI / pytest / JUnit XML / Allure / MCP / RAG / GitHub Actions
```

## 7. 面试官可能追问

### 1. 你的项目和普通自动化脚本有什么区别？

回答：

普通脚本只能运行测试。这个项目把测试执行、用例、接口、报告、失败分析、知识库和 AI 生成串成平台闭环。前端可以触发执行，后端解析报告，失败结果可以继续进入 AI 分析和 Bug 报告生成。

### 2. 为什么要用 RAG？

回答：

测试用例生成必须依赖需求、接口文档、历史 Bug、日志和测试报告。如果只让大模型凭空生成，结果可能不符合项目事实。RAG 可以把这些资料作为上下文传入，让生成结果更可解释，也能返回 source_id 方便追溯。

### 3. 为什么保留 Streamlit，又新增 Vue？

回答：

Streamlit 适合快速做内部 demo，但真实测试平台通常是前后端分离。为了体现全栈能力，我新增了 Vue + FastAPI；Streamlit 保留为旧版演示入口，避免破坏原有功能。

### 4. 现在的 RAG 是真正向量检索吗？

回答：

当前 Vue 知识库页面为了保证本地可演示，先使用稳定的关键词检索服务。项目原来保留了向量库和 RAG 相关模块，后续可以把 `search_knowledge_contexts` 内部替换为 Chroma / FAISS / Milvus，不影响前端和 API 结构。

### 5. 自动化执行怎么保证安全？

回答：

当前只允许执行平台预定义的 scenario_id，例如 `api_login`、`api_file_upload`，不会让用户从页面传任意 shell 命令。后端根据白名单场景映射 pytest 目标，减少命令注入风险。

### 6. Allure 在项目里起什么作用？

回答：

pytest 执行后会生成 JUnit XML 和 Allure-compatible results。JUnit XML 方便程序解析统计，Allure 用于生成更适合人工查看的 HTML 报告。CI 里也可以上传 Allure report artifact。

### 7. MCP tools 的意义是什么？

回答：

MCP tools 让平台能力可以被 Agent 调用，而不是只能点页面。例如 Agent 可以先调用 `retrieve_test_context` 检索需求，再调用 `generate_test_cases` 生成用例，然后调用 `run_api_tests` 执行，最后调用 `analyze_failure` 和 `generate_bug_report` 做失败分析。

### 8. 这个项目还有哪些不足？

回答：

当前更偏面试可演示 MVP，还不是企业级平台。主要不足是没有复杂权限系统、真实任务队列、真实向量数据库持久化、多环境管理和完整用例编辑流。后续我会优先补真实向量检索、异步执行队列、接口调试能力和更完整的测试计划管理。

如果面试官继续追问“和成熟平台差距在哪里”，可以补充：

- 目前 API 用例、环境、集合还是内置数据，下一步会落库并支持新增、编辑、删除。
- 当前自然语言编排是确定性 planner，后续可以接入 LLM，把操作计划转成真实平台动作。
- 当前 Web/性能测试还没有做到 FullScopeTest 那种完整工作台，后续计划补 Playwright 脚本管理、Locust/JMeter 性能场景和统一报告中心。

## 8. 推荐演示命令

启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

启动前端：

```powershell
cd frontend\qualitypilot-web
npm.cmd run dev
```

运行 demo：

```powershell
.\.venv\Scripts\python.exe scripts\run_qualitypilot_demo.py
```

运行自动化场景：

```powershell
.\.venv\Scripts\python.exe scripts\run_automation_suite.py --scenario api_login
```

检查质量：

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest tests\unit -v
cd frontend\qualitypilot-web
npm.cmd run build
```

## 9. 讲项目时不要夸大的点

- 不要说这是完整企业级测试平台。
- 不要说已经实现任意接口调试能力，目前更偏接口目录 + 预定义 pytest 场景。
- 不要说当前知识库页面已经是生产级向量检索，应该说服务层已经按 RAG 流程设计，当前 demo 使用稳定关键词检索，后续可替换向量库。
- 不要说 UI 自动化已经覆盖真实浏览器全流程，当前主要是 dry-run adapter 和扩展思路。

## 10. 下一步增强方向

1. 把关键词检索替换为 Chroma / FAISS 向量检索。
2. 引入后台任务队列，避免 pytest 执行阻塞 API 请求。
3. 增加测试计划，把多个场景组合成一次执行。
4. 增加失败趋势图、模块质量分布、历史执行对比。
5. 增加用例编辑和导出能力。

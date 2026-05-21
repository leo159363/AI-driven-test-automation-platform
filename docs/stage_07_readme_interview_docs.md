# Stage 7：README、功能图与面试文档

## 本阶段目标

把 QualityPilot 从“功能已经能跑”的工程，整理成更适合投简历和面试展示的项目：

- README 第一屏讲清楚项目定位。
- 加入 Vue 版功能图，避免只看文字。
- 整理启动方式和演示路线。
- 新增面试讲解手册，帮助回答面试官追问。

## 本阶段完成内容

### 1. README 重写

新版 README 强调：

- 项目定位：基于 MCP + RAG 的智能自动化测试平台。
- 核心闭环：知识入库 -> RAG 检索 -> 用例生成 -> pytest 执行 -> 报告解析 -> 失败分析 -> Bug 报告。
- 技术栈：Vue 3、FastAPI、pytest、Allure、MCP、RAG、GitHub Actions。
- 快速启动：Python 依赖、Vue 依赖、FastAPI、Vue、一键启动。
- 推荐演示路线：从 API 测试中心讲到 AI 测试助手。
- 后端接口清单和 MCP tools 清单。
- 当前边界：不夸大为企业级平台。

### 2. 功能图新增

新增三个 Vue 功能图：

- `docs/assets/screenshots/vue-api-testing-center.svg`
- `docs/assets/screenshots/vue-automation-report.svg`
- `docs/assets/screenshots/vue-knowledge-rag.svg`

这些图用于 README 展示：

- API 测试中心
- 自动化执行与报告
- 知识库与 RAG 检索

### 3. 面试讲解手册

新增：

- `docs/interview_playbook.md`

内容包括：

- 30 秒项目介绍
- 2 分钟讲解流程
- 核心架构
- 每个功能模块怎么讲
- 简历写法
- 面试官可能追问
- 推荐演示命令
- 不要夸大的点
- 后续增强方向

## 推荐使用方式

准备面试时建议按这个顺序看：

1. `README.md`
2. `docs/interview_playbook.md`
3. `docs/mcp_tools.md`
4. `docs/stage_01_fastapi_backend.md` 到 `docs/stage_07_readme_interview_docs.md`

## 面试时重点讲什么

不要只讲“我用了 AI”。应该讲：

1. 为什么测试用例生成需要 RAG 上下文。
2. 自动化测试如何从页面触发到 pytest 执行。
3. JUnit / Allure 报告如何被平台消费。
4. MCP tools 如何把平台能力暴露给 Agent。
5. 当前 MVP 的边界在哪里，下一步如何增强。

## 验证方式

本阶段主要是文档和静态功能图更新，验证项：

```powershell
.\.venv\Scripts\python.exe -m ruff check src\api tests\unit\test_api_app.py tests\unit\test_knowledge_service.py
.\.venv\Scripts\python.exe -m pytest tests\unit\test_api_app.py tests\unit\test_knowledge_service.py tests\unit\test_assistant_service.py -v
cd frontend\qualitypilot-web
npm.cmd run build
```

## 下一阶段建议

Stage 8 建议优先做“接口调试与断言配置”的 MVP：

- 在 API 测试中心增加请求编辑区。
- 支持 method、url、headers、body 输入。
- 后端增加受控的 HTTP request runner。
- 支持状态码断言和 JSON 字段断言。

这样项目会更接近你截图里那类 Postman / Apifox / 自动化测试平台。

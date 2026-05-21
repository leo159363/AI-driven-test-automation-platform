# Stage 6：知识库与 RAG 页面

## 本阶段目标

把 Vue 里的“知识库管理”从占位页改成可操作页面，让面试时能讲清楚 AI 不是凭空生成，而是基于测试知识上下文：

```text
文档上传 -> 文本切分 -> 元数据标注 -> 知识检索 -> 用例生成 / 失败分析 / Bug 报告
```

## 已完成能力

1. 新增 FastAPI 知识库接口：
   - `GET /api/knowledge/source-types`
   - `GET /api/knowledge/sources`
   - `POST /api/knowledge/search`
   - `POST /api/knowledge/upload`

2. 新增知识库服务层：
   - 内置登录鉴权、文件上传、历史 Bug、测试规范等 demo 知识片段。
   - 支持 `project`、`module`、`version`、`source_types`、`top_k` 过滤。
   - 支持上传 `txt` / `markdown` 文档并切分为 chunk。
   - 上传内容保存到 `data/qualitypilot_knowledge/documents.json`，该目录不纳入 Git。

3. Vue 知识库页面：
   - 支持查看知识来源列表。
   - 支持选择 source type。
   - 支持上传文档并入库。
   - 支持输入 Query 做 RAG 检索测试。
   - 展示召回片段的 `source_id`、`source_type`、`title`、`score`、`metadata` 和正文。

4. AI 测试助手复用知识库检索服务：
   - `AI 测试助手` 和 `知识库管理` 使用同一套本地检索服务。
   - 后续把关键词检索替换为向量检索时，两个页面可以同时受益。

## 当前实现边界

当前检索是稳定可演示的关键词重叠检索，不是真正 embedding + 向量数据库检索。这样做的原因是：

- 面试 demo 不依赖外部模型 Key。
- 本地运行稳定，能先把完整测试开发闭环跑通。
- 服务层接口已经按 RAG 结构设计，后续可以把 `search_knowledge_contexts` 内部替换为 Chroma / FAISS / Milvus。

## 手动验证

启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

查看接口文档：

```text
http://127.0.0.1:8000/docs
```

启动 Vue：

```powershell
cd frontend\qualitypilot-web
npm.cmd run dev
```

访问页面：

```text
http://127.0.0.1:5173/knowledge
```

推荐演示流程：

1. 打开“知识库管理”。
2. 先查看内置知识来源。
3. 上传一个 markdown 需求文档。
4. 输入 Query，例如“登录接口 token 401 错误处理和用例设计”。
5. 查看召回片段。
6. 切到“AI 测试助手”，说明它会复用这些上下文生成测试产物。

## 面试讲法

这一阶段体现的是测试开发平台里的“测试知识资产管理”和“RAG 上下文检索”能力。测试用例生成、失败分析、Bug 报告生成如果没有上下文，很容易变成普通聊天；引入知识库后，可以把需求、接口文档、历史缺陷、日志和测试报告作为证据来源，生成结果更容易解释和追溯。

## 下一阶段建议

优先做 Stage 7：README、截图、面试文档。

原因：

- 当前后端、Vue、API 测试中心、自动化执行、AI 助手、知识库页面已经形成可演示闭环。
- 下一步应该把启动步骤、功能截图、演示流程和面试话术整理出来，帮助项目更适合投简历和面试讲解。

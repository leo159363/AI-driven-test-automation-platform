# Stage 13: FullScope 风格平台模块融合

## 背景

本阶段参考 FullScopeTest 的平台模块划分，但没有整仓复制其源码。

原因：

- FullScopeTest 仓库 README 中展示了 MIT badge，但仓库根目录没有实际 `LICENSE` 文件。
- QualityPilot 是公开简历项目，直接复制第三方源码会带来许可、署名和面试解释风险。
- 当前项目的核心差异化是 MCP + RAG + pytest + Allure + AI 失败分析，不能被改成另一个项目的简单副本。

## 本阶段完成内容

新增后端平台接口：

- `GET /api/platform/workspace`
- `GET /api/platform/web-tests/scripts`
- `GET /api/platform/app-tests/scripts`
- `GET /api/platform/performance/scenarios`
- `GET /api/platform/cicd/jobs`
- `GET /api/platform/documents`
- `GET /api/platform/settings`

新增前端页面：

- Web 自动化测试
- App 测试
- 性能测试
- CI/CD 与定时任务
- 测试文档
- 系统设置

修复：

- 当用户误打开 FastAPI 后端地址 `http://127.0.0.1:8000/api-testing` 时，自动跳转到 Vue 前端 `http://127.0.0.1:5173/api-testing`。

## 和 FullScopeTest 的对应关系

| FullScopeTest 模块 | QualityPilot 对应实现 | 差异化 |
| --- | --- | --- |
| API 接口测试 | 接口测试工作台 | 增加 RAG 上下文、MCP tools、pytest 映射 |
| Web 自动化 | Web 自动化测试 | 以 Playwright + pytest + AI 失败自愈为主 |
| App 测试 | App 测试 | 当前先做移动端接口契约和兼容性场景 |
| 性能测试 | 性能测试 | 保留 Locust 思路，增加瓶颈和风险说明 |
| 测试报告 | 测试报告 | 结合 JUnit XML、Allure 目录和失败分析 |
| CI/CD | CI/CD 与定时任务 | 体现质量门禁、夜间回归、失败分析队列 |
| 测试文档 | 测试文档 + 知识库管理 | 文档可以进入 RAG 知识库 |
| AI Copilot | AI 测试助手 | 使用 MCP tools 组织测试开发工作流 |

## 验证

已通过：

```powershell
.\.venv\Scripts\python.exe -m ruff check src\api\main.py src\api\routers\platform.py tests\unit\test_api_app.py
.\.venv\Scripts\python.exe -m pytest tests\unit\test_api_app.py tests\unit\test_api_debug_service.py -v
cd frontend\qualitypilot-web
npm.cmd run build
```

结果：

- Ruff 通过
- 单元测试 32 passed
- Vue production build 通过

## 下一阶段建议

下一阶段应该把这些页面从“平台模块展示”推进到“可操作闭环”：

1. Web 自动化页面增加“运行脚本”按钮，调用后端 pytest 执行接口。
2. 性能测试页面增加 Locust 结果解析样例。
3. CI/CD 页面增加 GitHub Actions workflow 文件和 README 截图。
4. AI 测试助手增加“把生成用例沉淀到测试用例列表”的操作。

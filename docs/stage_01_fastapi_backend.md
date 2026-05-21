# Stage 1：FastAPI 后端骨架

## 本阶段目标

把 QualityPilot 从只有 Python Dashboard 的演示项目，推进为具备正式后端 API 的全栈项目。当前阶段不重写 RAG、MCP、pytest、Allure 逻辑，只把已有能力封装成 Vue 后续可以调用的 HTTP API。

## 已完成接口

| 接口 | 说明 |
| --- | --- |
| `GET /api/health` | 健康检查，供前端和 CI 判断后端是否可用 |
| `GET /api/test-cases` | 返回当前内置测试用例目录和统计信息 |
| `GET /api/api-endpoints` | 返回接口测试目录，关联已有自动化用例 |
| `GET /api/automation/scenarios` | 返回 pytest 自动化场景和执行命令 |
| `GET /api/reports/latest` | 返回 JUnit XML、Allure results、Allure HTML report 的发现结果 |

## 启动方式

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

接口文档地址：

```text
http://127.0.0.1:8000/docs
```

## 阶段重点

- FastAPI 只是 API 层，不替换现有 RAG/MCP/pytest 逻辑。
- Vue 前端后续只需要调用 JSON 接口，不再直接依赖 Streamlit 页面。
- 上传接口目录已和现有自动化脚本保持一致，统一使用 `/api/upload`。

## 下一阶段

Stage 2 应该新增 `frontend/qualitypilot-web/`，使用 Vue 3 + Vite + TypeScript 搭建前端骨架，并先对接本阶段的基础接口。

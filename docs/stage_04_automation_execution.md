# Stage 4：自动化执行与报告

## 本阶段目标

让 Vue 页面可以触发后端执行 pytest 自动化场景，并看到 JUnit / Allure 报告路径、执行状态和执行历史。

## 已完成能力

| 能力 | 说明 |
| --- | --- |
| `POST /api/automation/run` | 执行一个内置 pytest 场景 |
| `GET /api/automation/runs` | 查看历史执行记录 |
| `GET /api/reports/{run_id}` | 查看一次执行的报告详情 |
| Vue 自动化执行页 | 选择场景、点击执行、查看最新结果和历史 |
| Vue 测试报告页 | 展示从 API 触发的自动化执行记录 |
| 全栈启动脚本 | 使用一个 Python 命令同时启动 FastAPI 和 Vue |

## 启动方式

首次进入前端目录安装依赖：

```powershell
cd frontend\qualitypilot-web
npm.cmd install
cd ..\..
```

之后可以用一个命令启动前后端：

```powershell
.\.venv\Scripts\python.exe scripts\start_fullstack.py
```

访问：

```text
Vue 前端：http://127.0.0.1:5173
FastAPI 文档：http://127.0.0.1:8000/docs
```

## 报告产物

从 Vue 页面触发执行后，会生成：

```text
reports/api-runs/{run_id}/junit.xml
reports/api-runs/{run_id}/allure-results/
reports/api-runs/{run_id}/run.json
```

## 下一阶段

Stage 5 应该做 `AI 测试助手 / LLM 对话中心`：提示词模板、知识库开关、RAG 检索上下文、用例生成、失败分析和 Bug 报告草稿。

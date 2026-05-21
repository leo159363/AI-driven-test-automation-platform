# Stage 2：Vue 前端工程骨架

## 本阶段目标

新增 `frontend/qualitypilot-web/`，让 QualityPilot 具备真正的前端工程入口。当前阶段重点是布局、路由和 API 调用层，不做复杂业务写入能力。

## 已完成页面

| 页面 | 当前能力 |
| --- | --- |
| 平台总览 | 调用 FastAPI 汇总测试用例、接口、自动化场景和报告产物 |
| API 测试 | 展示接口目录、接口列表、请求示例、断言和关联用例 |
| 测试用例 | 展示用例目录、类型筛选、pytest 目标 |
| 自动化执行 | 展示 pytest 场景和执行命令 |
| 测试报告 | 展示 JUnit / Allure 报告发现结果 |
| AI 测试助手 | 先完成页面结构，后续接入 RAG 和 MCP tools |
| 知识库管理 | 先完成页面结构，后续接入文档上传和检索 |

## 启动方式

先启动 FastAPI：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

再启动 Vue：

```powershell
cd frontend\qualitypilot-web
npm.cmd install
npm.cmd run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

## 阶段重点

- Vue 通过 `src/services/api.ts` 调用 FastAPI，不直接调用 Python 内部函数。
- 当前页面已具备平台导航和业务骨架，后续可以逐页增强。
- 保留 Streamlit Dashboard，避免一次性重写破坏已有演示链路。

## 下一阶段

Stage 3 应该增强 `API 测试中心`：接口树、接口详情、关联用例、最近执行状态、断言展示和运行入口。

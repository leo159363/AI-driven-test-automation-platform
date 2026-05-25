# Stage 09：参考 FullScopeTest 增强 API 测试工作台

## 一、本阶段目标

把 QualityPilot 的 API 测试中心从“接口目录 + 简单调试”升级成更接近真实测试平台的工作台。参考对象是 FullScopeTest 的 API 测试、环境管理、Mock、AI 用例生成和自然语言编排思路，但不复制其代码实现。

QualityPilot 本阶段保留自己的技术路线：

- 前端：Vue 3 + Vite + TypeScript
- 后端：FastAPI + Pydantic
- 差异化：继续服务于 RAG / MCP / pytest / Allure 的测试开发闭环

## 二、已实现功能

### 1. API 环境管理

新增接口：

```text
GET /api/api-testing/environments
```

返回内置环境：

- `mock-local`：默认 Mock 环境，不请求真实服务，适合稳定演示。
- `local-api`：本机 API 环境，只允许请求 `localhost` / `127.0.0.1`。

环境支持：

- `base_url`
- 公共 `headers`
- `variables`
- Postman 风格 `{{variable}}` 占位符替换

### 2. 请求调试增强

`POST /api/api-testing/debug` 支持：

- method
- path
- base_url
- headers
- query params
- body
- body_type
- environment
- mock_config
- expected_status
- JSON path assertions

安全限制：

- 默认走内置 Mock。
- 真实 HTTP 调试只允许 `localhost`、`127.0.0.1`、`::1`，避免页面变成任意 SSRF 请求工具。

### 3. 自定义 Mock 响应

前端可以直接配置：

- status code
- delay ms
- response body

后端返回：

- status code
- headers
- raw body
- JSON body
- duration
- assertion summary

### 4. AI 用例裂变

新增接口：

```text
POST /api/api-testing/synthesize
```

当前为确定性实现，先保证演示稳定，可生成：

- 正常路径
- 异常密码
- 缺少字段
- 空值
- SQL 注入类输入
- XSS 类输入
- 文件上传缺少文件名

这部分借鉴 FullScopeTest 的数据合成思路，但实现为 QualityPilot 自己的 FastAPI service。

### 5. 自然语言编排预览

新增接口：

```text
POST /api/api-testing/plan
```

输入类似：

```text
帮我为登录接口创建测试集合，生成正常登录和异常登录用例，并执行集合
```

返回操作计划：

- `create_environment`
- `create_collection`
- `create_case`
- `run_collection`

当前还只是 plan preview，后续阶段会把计划落到真实用例库和执行队列。

### 6. cURL 导出

新增接口：

```text
POST /api/api-testing/curl
```

支持把当前请求导出成 cURL，并替换环境变量、拼接 query params。

## 三、前端页面变化

API 测试页面新增：

- 接口目录
- 接口列表
- 环境选择
- 环境变量编辑
- 公共 Headers 编辑
- Query Params 编辑
- Request Body 编辑
- 自定义 Mock 响应
- 状态码断言
- JSON 字段断言
- 响应体和断言结果
- cURL 命令预览
- AI 数据裂变结果列表
- AI 编排计划预览

页面结构更接近 Postman / Apifox / FullScopeTest 一类 API 测试工作台。

## 四、修改文件

```text
src/api/services/api_debug_service.py
src/api/routers/api_testing.py
frontend/qualitypilot-web/src/views/ApiTestingView.vue
frontend/qualitypilot-web/src/services/api.ts
frontend/qualitypilot-web/src/types.ts
frontend/qualitypilot-web/src/styles.css
tests/unit/test_api_debug_service.py
tests/unit/test_api_app.py
README.md
docs/interview_playbook.md
docs/stage_09_fullscopetest_api_workspace.md
```

## 五、验证方式

后端静态检查：

```powershell
.\.venv\Scripts\python.exe -m ruff check src\api tests\unit\test_api_app.py tests\unit\test_api_debug_service.py
```

后端单元测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_api_debug_service.py tests\unit\test_api_app.py -v
```

前端构建：

```powershell
cd frontend\qualitypilot-web
npm.cmd run build
```

## 六、和 FullScopeTest 的区别

FullScopeTest 更偏完整测试管理系统，包含 Flask 后端、React 前端、Celery 任务、Web 自动化、性能测试和全局 Copilot。

QualityPilot 本阶段只复现最适合测试开发实习面试的 API 工作台能力：

- 环境变量
- 接口调试
- Mock
- 断言
- AI 用例生成
- 编排计划
- cURL 导出

差异化能力是：

- MCP tools 可被 Agent 调用
- RAG 知识库可以为测试设计、失败分析、Bug 报告提供上下文
- pytest / Allure 是平台执行闭环的一部分

## 七、后续阶段

下一阶段建议做“测试资产持久化与用例管理增强”：

- 新增接口集合、接口用例、环境配置的数据模型。
- 前端支持新增、编辑、删除 API 用例。
- AI 裂变出的用例可以保存到测试用例库。
- 自动化执行页面可以选择保存后的用例集合运行。

这个阶段做完后，项目会更接近 FullScopeTest 的测试管理能力，同时仍保持 QualityPilot 的 RAG/MCP 差异化。

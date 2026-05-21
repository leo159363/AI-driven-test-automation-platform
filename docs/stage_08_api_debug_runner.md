# Stage 8：接口调试与断言配置 MVP

## 本阶段目标

让 `API 测试` 页面更接近 Postman / Apifox / 自动化测试平台的核心观感：选择接口后，可以编辑 headers、body、断言，点击发送请求，查看响应和断言结果。

## 已完成能力

### 1. 后端受控 API Debug Runner

新增接口：

```text
POST /api/api-testing/debug
```

能力：

- 支持 method、path、headers、body。
- 支持期望状态码断言。
- 支持 JSON Path 断言：
  - `equals`
  - `contains`
  - `exists`
  - `not_exists`
- 默认使用内置 mock 目标，避免额外启动业务服务。
- 如果填写 `base_url`，只允许 `localhost / 127.0.0.1 / ::1`，避免变成任意外部请求工具。

### 2. 内置 Mock 接口

当前内置两个测试开发面试常见接口：

| 接口 | 场景 |
| --- | --- |
| `POST /api/login` | 登录成功、密码错误、参数缺失 |
| `POST /api/upload` | 文件上传成功、缺少文件名 |

### 3. Vue API 测试页面增强

`API 测试` 页面现在支持：

- 接口目录
- 接口列表
- 请求调试器
- Headers JSON 编辑
- Request Body 编辑
- 状态码断言
- JSON 字段断言
- 响应体展示
- 断言通过 / 失败结果展示

## 使用方式

启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

启动前端：

```powershell
cd frontend\qualitypilot-web
npm.cmd run dev
```

打开：

```text
http://127.0.0.1:5173/api-testing
```

推荐体验：

1. 左侧选择 `登录鉴权 -> 登录成功`。
2. 保持 `目标 Base URL` 为空，使用内置 Mock。
3. 检查 Headers 和 Request Body。
4. 检查断言：
   - `status == 200`
   - `token exists`
   - `user.username equals tester`
5. 点击 `发送请求并执行断言`。
6. 查看响应体和断言结果。

再选择 `登录失败` 或 `文件上传参数错误`，可以看到错误响应和断言结果。

## 面试讲法

可以这样讲：

> 这一阶段我补了接口调试能力。传统自动化平台不只是展示用例，还应该能围绕接口做请求、断言和结果展示。我这里没有开放任意命令执行，而是做了受控 API runner。默认使用内置 mock 目标，保证本地 demo 稳定；如果要请求真实服务，只允许 localhost，避免安全风险。断言先支持状态码和 JSON 字段，后续可以扩展响应时间、header、schema 校验和数据库校验。

## 当前边界

- 当前不是完整 Postman，只是接口调试 MVP。
- 暂不支持文件选择上传，文件上传接口先用文本 body 模拟二进制内容。
- JSON Path 目前支持简单点号路径，例如 `user.username`。
- 暂不支持环境变量、前置脚本、后置脚本。

## 下一阶段建议

Stage 9 建议做“测试计划与批量执行”：

- 选择多个接口 / 场景组成测试计划。
- 一键批量执行。
- 展示计划级通过率、失败接口、报告路径。
- 把 API 调试结果和 pytest 自动化执行结果统一到执行历史里。

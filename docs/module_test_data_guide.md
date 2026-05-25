# QualityPilot 各模块怎么用、填什么、测什么

这份文档按页面说明：每个模块怎么用、应该用哪个用例测试、页面里的输入框填什么。

## 1. API 测试中心

这个页面是最重要的。它用来演示“接口测试平台”的能力：选择接口、填写请求数据、发送请求、查看断言结果、生成 AI 裂变用例。

### 1.1 登录成功用例

左侧选择：

```text
登录鉴权 -> 登录成功
```

字段这样填：

| 字段 | 填什么 | 为什么 |
| --- | --- | --- |
| 环境 | 内置 Mock 环境 | 不需要真实后端，适合演示 |
| Base URL | 留空 | 留空表示走内置 Mock |
| Body Type | json | 登录请求体是 JSON |
| 环境变量 JSON | 保持默认 | 提供 username/password 变量 |
| 环境公共 Headers JSON | `{"Content-Type": "application/json"}` | 公共请求头 |
| 请求 Headers JSON | `{"Content-Type": "application/json"}` | 当前接口请求头 |
| Query Params JSON | `{}` | 登录接口不需要 query 参数 |
| Request Body | `{"username": "tester", "password": "Passw0rd!"}` | 正确账号密码 |
| 期望状态码 | `200` | 登录成功 |
| JSON 断言 1 | `token exists` | 响应里必须有 token |
| JSON 断言 2 | `user.username equals tester` | 校验用户信息 |

预期结果：

```json
{
  "token": "demo-token",
  "user": {
    "username": "tester"
  }
}
```

面试怎么讲：

```text
这是登录鉴权主流程。我用状态码断言和 JSON 字段断言验证登录成功后返回 token。
```

注意：

```text
不要选“本机 API 环境”，除非你自己另外启动了 127.0.0.1:9000 的真实接口服务。
面试演示时统一选“内置 Mock 环境”，Base URL 留空。
```

### 1.2 登录失败用例

左侧选择：

```text
登录鉴权 -> 登录失败
```

字段这样填：

| 字段 | 填什么 |
| --- | --- |
| 环境 | 内置 Mock 环境 |
| Base URL | 留空 |
| Body Type | json |
| 请求 Headers JSON | `{"Content-Type": "application/json"}` |
| Query Params JSON | `{}` |
| Request Body | `{"username": "tester", "password": "wrong"}` |
| 期望状态码 | `401` |
| JSON 断言 | `error equals invalid_credentials` |

预期结果：

```json
{
  "error": "invalid_credentials"
}
```

面试怎么讲：

```text
这是异常流测试。错误密码不能返回 token，应该返回 401 和统一错误码，避免泄露账号状态。
```

### 1.3 文件上传成功用例

左侧选择：

```text
文件上传 -> 文件上传成功
```

字段这样填：

| 字段 | 填什么 |
| --- | --- |
| 环境 | 内置 Mock 环境 |
| Base URL | 留空 |
| Body Type | raw |
| 请求 Headers JSON | `{"Content-Type": "application/octet-stream", "X-Filename": "demo.txt"}` |
| Query Params JSON | `{}` |
| Request Body | `demo-binary-content` |
| 期望状态码 | `201` |
| JSON 断言 1 | `filename equals demo.txt` |
| JSON 断言 2 | `size exists` |

预期结果：

```json
{
  "filename": "demo.txt",
  "size": 19
}
```

面试怎么讲：

```text
这是文件上传接口的主流程。这里用 raw body 模拟二进制文件内容，用 X-Filename 传文件名。
```

### 1.4 文件上传参数错误用例

左侧选择：

```text
文件上传 -> 文件上传参数错误
```

字段这样填：

| 字段 | 填什么 |
| --- | --- |
| 环境 | 内置 Mock 环境 |
| Base URL | 留空 |
| Body Type | raw |
| 请求 Headers JSON | `{"Content-Type": "application/octet-stream"}` |
| Query Params JSON | `{}` |
| Request Body | `demo-binary-content` |
| 期望状态码 | `400` |
| JSON 断言 | `error equals missing_filename` |

预期结果：

```json
{
  "error": "missing_filename"
}
```

面试怎么讲：

```text
这是参数校验用例。故意不传 X-Filename，验证接口是否能识别缺失参数并返回明确错误。
```

### 1.5 AI 裂变用例怎么用

先选择 `登录成功`，然后点：

```text
AI 裂变用例
```

它会生成：

- 正常登录
- 错误密码
- 缺少密码字段
- 空用户名
- SQL 注入密码
- XSS 用户名

你可以点某一条下面的：

```text
应用到调试器
```

它会自动把 Request Body、期望状态码和断言填进去。

面试怎么讲：

```text
AI 裂变用例不是直接替代测试人员，而是基于一个接口样例，扩展出异常、边界和安全类测试数据。
```

## 2. 测试用例模块

这个页面不用填数据。

你只需要点：

```text
全部 / 接口测试 / 界面测试
```

看用例表里的：

- 用例 ID
- 标题
- 类型
- 模块
- 优先级
- pytest 目标

面试怎么讲：

```text
这个页面展示测试资产管理能力。每个用例都关联到 pytest 自动化目标，后续可以从平台触发执行。
```

## 3. 自动化执行模块

这个页面用来触发 pytest。

推荐先选：

```text
API: 登录接口
```

然后点：

```text
执行选中场景
```

第二个可以选：

```text
API: 文件上传接口
```

执行后看：

- run_id
- 状态 passed / failed
- 总数
- 通过
- 失败
- JUnit XML 路径
- Allure results 路径

面试怎么讲：

```text
前端没有直接执行命令，而是把 scenario_id 发给 FastAPI。
后端根据白名单场景映射 pytest 目标，避免用户从页面传任意 shell 命令。
```

## 4. 测试报告模块

这个页面不用填数据。

使用前先在 `自动化执行` 页面跑一次：

```text
API: 登录接口
```

然后回到 `测试报告` 看：

- 自动化运行记录
- JUnit XML
- Allure results
- 通过 / 失败统计

面试怎么讲：

```text
自动化测试平台不能只运行测试，还要解析和展示测试报告。
JUnit XML 适合程序解析，Allure results 适合生成可读报告。
```

## 5. 知识库管理模块

这个页面用来演示 RAG。

过滤条件保持默认：

| 字段 | 填什么 |
| --- | --- |
| 项目 | `QualityPilot` |
| 模块 | 留空 |
| 版本 | `demo` |
| source_type | 默认勾选即可 |
| 召回数量 | `5` |

检索框可以输入：

```text
登录接口 token 401 错误处理和用例设计
```

也可以输入：

```text
文件上传缺少文件名应该怎么设计测试用例
```

面试怎么讲：

```text
这里模拟把需求、接口文档、历史 Bug、测试报告和规范作为知识来源。
AI 生成用例或分析失败前，先通过 RAG 检索相关上下文，避免凭空生成。
```

上传文档可以先不演示。面试时间有限时，重点演示检索即可。

## 6. AI 测试助手模块

这个页面用于生成测试产物。

### 6.1 智能用例生成

模板选择：

```text
智能用例生成
```

字段这样填：

| 字段 | 填什么 |
| --- | --- |
| 项目 | `QualityPilot` |
| 模块 | `登录鉴权` |
| 版本 | `demo` |
| 启用知识库上下文 | 勾选 |
| 召回数量 | `4` |
| source_type | `requirement`、`api_doc`、`test_case`、`bug`、`standard` |

输入内容：

```text
登录接口支持账号密码登录，成功返回 token，错误密码返回 401，请生成接口测试用例。
```

点击：

```text
生成测试产物
```

### 6.2 失败原因分析

模板选择：

```text
失败原因分析
```

输入内容：

```text
登录接口自动化用例失败，期望状态码 200，实际返回 401，响应体为 {"error": "invalid_credentials"}，请分析可能原因。
```

### 6.3 Bug 报告生成

模板选择：

```text
Bug 报告生成
```

输入内容：

```text
文件上传接口缺少 X-Filename 时返回 500，预期应该返回 400 missing_filename，请生成 Bug 报告。
```

面试怎么讲：

```text
AI 助手不是普通聊天，而是围绕测试开发任务做了模板化输入和结构化输出。
它能结合 RAG 上下文生成用例、失败分析和 Bug 报告草稿。
```

## 7. 你最应该练的演示顺序

只练这一条主线：

```text
API 测试中心：登录成功 -> 发送请求
API 测试中心：登录失败 -> 发送请求
API 测试中心：AI 裂变用例 -> 应用一个异常用例
自动化执行：API 登录接口 -> 执行
测试报告：查看运行记录和报告路径
知识库管理：检索 login token 401
AI 测试助手：生成登录接口测试用例
```

这条线练熟之后，你就能讲清楚：

- 接口测试怎么设计
- 自动化怎么执行
- 报告怎么解析
- RAG 怎么提供上下文
- AI 怎么辅助测试开发

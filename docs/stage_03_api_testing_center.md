# Stage 3：API 测试中心增强

## 本阶段目标

把 Vue 的 `API 测试` 页面从普通接口列表增强为更接近 Postman / Apifox / WHartTest 的接口测试工作台。当前阶段仍然不做任意接口调试器，优先绑定现有 pytest 自动化场景，保证面试演示可以讲清楚。

## 已完成能力

| 能力 | 说明 |
| --- | --- |
| 接口目录树 | 按模块展示登录鉴权、文件上传等接口测试资产 |
| 接口列表 | 展示接口名称、method、path、模块、关联用例和自动化状态 |
| 接口详情 | 展示接口描述、headers、request body、断言、关联用例 |
| pytest 关联 | 展示每个接口用例对应的 pytest target |
| 运行入口占位 | 展示运行命令，Stage 4 会改成页面点击触发执行 |
| 后端结构化输出 | `/api/api-endpoints` 返回前端可直接渲染的字段 |

## 后端接口字段

`GET /api/api-endpoints` 的 `items` 中包含：

```json
{
  "endpoint_id": "api-login-success",
  "name": "登录成功",
  "module": "登录鉴权",
  "method": "POST",
  "path": "/api/login",
  "description": "验证正确账号密码可以获得认证令牌，是登录鉴权模块的主流程接口。",
  "headers": {"Content-Type": "application/json"},
  "request_body": "{\"username\": \"tester\", \"password\": \"Passw0rd!\"}",
  "assertions": ["HTTP 状态码为 200", "响应体包含 token"],
  "related_case_id": "TC-API-LOGIN-001",
  "scenario_id": "api_login",
  "pytest_target": "tests/automation/test_api_login.py::test_api_login_success",
  "automation_status": "已自动化"
}
```

## 下一阶段

Stage 4 应该新增后端执行接口，并让 Vue 页面点击按钮触发 pytest 自动化执行，然后展示 JUnit / Allure 报告路径和通过失败统计。

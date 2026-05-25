# Stage 12：修复 API 测试页点击发送无明显反馈

## 一、问题现象

用户在 API 测试页点击发送后，页面看起来没有反应，后端日志出现：

```text
POST /api/api-testing/debug HTTP/1.1" 400 Bad Request
```

## 二、根因

当前页面选择了：

```text
本机 API 环境
```

Base URL 是：

```text
http://127.0.0.1:9000
```

如果本机没有启动 9000 端口的真实接口服务，请求会连接失败。之前后端把这个连接失败直接转成 400，前端又没有把失败原因放在请求工作台里，所以用户会感觉按钮没反应。

## 三、本阶段修复

### 1. 后端返回结构化连接失败结果

本机 HTTP 连接失败时，不再只返回 400，而是返回一次测试结果：

```json
{
  "error": "local_http_connection_failed",
  "message": "本机 HTTP 服务连接失败...",
  "url": "http://127.0.0.1:9000/api/login"
}
```

前端可以在响应区展示这个失败结果。

### 2. 前端增加发送状态反馈

请求工作台增加：

- 发送中提示
- 成功提示
- 断言失败提示
- 本机 API 连接失败提示

### 3. 增加切回内置 Mock 按钮

当 Base URL 不为空时，页面会提示当前正在请求本机真实服务，并显示：

```text
切回内置 Mock
```

点击后：

- 环境切回 `内置 Mock 环境`
- Base URL 清空
- 示例数据保留

## 四、使用建议

面试演示时统一使用：

```text
内置 Mock 环境
```

并保持：

```text
Base URL 留空
```

只有当你自己启动了真实接口服务时，才使用：

```text
本机 API 环境
```

## 五、验证

已执行：

```powershell
.\.venv\Scripts\python.exe -m ruff check src\api\services\api_debug_service.py tests\unit\test_api_debug_service.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_api_debug_service.py tests\unit\test_api_app.py -v
```

```powershell
cd frontend\qualitypilot-web
npm.cmd run build
```

结果：

```text
30 passed
Vue build passed
```

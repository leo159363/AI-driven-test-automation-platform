# Stage 10：修复 Vue 与 FastAPI 连接失败

## 一、问题现象

页面显示：

```text
Failed to fetch
```

并且 API 测试中心、平台总览里的统计数据都是 0 或 `--`。

## 二、根因

前端和后端没有真正连通。

具体原因有两个：

1. `scripts/start_fullstack.py` 之前把 HTTP `404` 也当成“服务可用”，如果 `8000` 端口被其他旧服务占用，它会误以为 FastAPI 已经启动。
2. Vue 前端之前默认写死请求 `http://127.0.0.1:8000`，一旦后端没启动、端口被占用或前端端口变化，就会直接 `Failed to fetch`。

## 三、本阶段修复

### 1. Vue 改为默认走 `/api`

前端默认请求相对路径：

```text
/api/health
/api/api-endpoints
```

开发环境由 Vite proxy 转发到 FastAPI。

### 2. Vite 增加 API 代理

`frontend/qualitypilot-web/vite.config.ts` 增加：

```text
/api -> http://127.0.0.1:8000
```

如果用 `scripts/start_fullstack.py --api-port 8010`，脚本会自动把代理目标切到 `8010`。

### 3. 启动脚本严格检查后端身份

启动脚本现在必须确认：

```json
{
  "status": "ok",
  "service": "qualitypilot-api"
}
```

只有这样才认为后端启动成功。

如果端口被旧服务占用，会给出明确提示，而不是继续打开一个空页面。

### 4. 启动脚本检查 Vue 的 `/api` 代理

即使 Vue 页面能打开，也必须确认：

```text
http://127.0.0.1:5173/api/health
```

能代理到 QualityPilot FastAPI。

否则脚本会提示关闭旧 Vue 终端，或换端口启动。

## 四、正确启动方式

推荐只用这一条：

```powershell
.\.venv\Scripts\python.exe scripts\start_fullstack.py
```

如果 8000 或 5173 被占用：

```powershell
.\.venv\Scripts\python.exe scripts\start_fullstack.py --api-port 8010 --web-port 5174
```

## 五、验证结果

本阶段已验证：

```text
GET http://127.0.0.1:8020/api/health
```

返回：

```json
{"status":"ok","service":"qualitypilot-api","version":"0.1.0","docs":"/docs"}
```

并验证：

```text
GET http://127.0.0.1:5175/api/api-endpoints
```

可以通过 Vue proxy 拿到 `/api/login` 接口数据。

## 六、你现在应该怎么做

先关闭之前打开的旧终端，尤其是：

- `npm.cmd run dev`
- `uvicorn src.api.main:app`
- 旧的 `scripts/start_fullstack.py`

然后重新运行：

```powershell
.\.venv\Scripts\python.exe scripts\start_fullstack.py
```

再打开：

```text
http://127.0.0.1:5173
```

如果还有端口占用，就换端口：

```powershell
.\.venv\Scripts\python.exe scripts\start_fullstack.py --api-port 8010 --web-port 5174
```

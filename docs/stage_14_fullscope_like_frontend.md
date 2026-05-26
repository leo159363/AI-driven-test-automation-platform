# Stage 14: FullScopeTest 风格前端重塑

## 本阶段目标

把 QualityPilot 的前端从普通卡片式 Demo，调整成更接近真实测试平台的工作台形态。

参考 FullScopeTest 的前端结构：

- 左侧可折叠菜单
- 顶部项目选择和全局搜索
- 接口测试模块带子菜单
- 接口测试页面采用请求工作台布局
- Web / App / 性能 / CI/CD 页面具备运行入口和结果展示

## 关键说明

没有直接复制 FullScopeTest 的 React 代码。

原因：

- FullScopeTest 前端是 React + Ant Design。
- QualityPilot 当前技术栈是 Vue 3 + Vite + TypeScript。
- 直接搬 React 文件会导致项目结构混乱，也不利于面试时解释。

本阶段做法是参考它的产品形态，用 Vue 重新实现。

## 完成内容

### 1. 主布局重塑

修改文件：

- `frontend/qualitypilot-web/src/App.vue`
- `frontend/qualitypilot-web/src/styles.css`

变化：

- 改成类似测试平台后台的布局。
- 左侧菜单支持折叠。
- 菜单增加层级：接口测试、Web 测试、App 测试、性能测试、CI/CD、测试文档、系统设置。
- 顶部增加项目选择、全局搜索、MCP/RAG/pytest 标签。

### 2. 接口测试工作台重塑

修改文件：

- `frontend/qualitypilot-web/src/views/ApiTestingView.vue`

变化：

- 左侧为测试用例 / 集合管理。
- 中间为请求编辑器。
- 请求区包含 method、path、环境、Base URL、Body Type。
- Tab 增加 Params、Headers、Body、前置脚本、断言脚本、Mock、说明。
- 下方展示响应、断言结果、AI 扩充用例、接口详情和 AI 编排。

### 3. 平台动作接口

修改文件：

- `src/api/routers/api_testing.py`
- `src/api/routers/platform.py`
- `frontend/qualitypilot-web/src/services/api.ts`
- `frontend/qualitypilot-web/src/types.ts`

新增能力：

- API 集合查询
- API 用例草稿保存
- API 集合运行
- Web 脚本运行
- App 契约检查运行
- 性能压测运行
- CI/CD 任务运行
- Dashboard 数据
- 全局搜索
- Copilot 对话

### 4. Web / App / 性能 / CI/CD 页面增强

修改文件：

- `frontend/qualitypilot-web/src/views/WebTestingView.vue`
- `frontend/qualitypilot-web/src/views/AppTestingView.vue`
- `frontend/qualitypilot-web/src/views/PerformanceView.vue`
- `frontend/qualitypilot-web/src/views/CicdView.vue`

变化：

- 页面按钮不再只是展示，已接入后端 demo run 接口。
- 点击运行后显示状态、通过数、命令或性能指标。

## 验证

已通过：

```powershell
.\.venv\Scripts\python.exe -m ruff check src\api\routers\api_testing.py src\api\routers\platform.py tests\unit\test_api_app.py
.\.venv\Scripts\python.exe -m pytest tests\unit\test_api_app.py tests\unit\test_api_debug_service.py -v
cd frontend\qualitypilot-web
npm.cmd run build
```

结果：

- Ruff 通过
- 单元测试 35 passed
- Vue production build 通过

## 下一阶段建议

下一阶段优先做首页 Dashboard。

原因：

- FullScopeTest 的首页有统计卡片、趋势图、类型分布、最近执行。
- QualityPilot 当前首页还不够像完整平台。
- 首页是面试官打开项目后的第一印象。

建议下一步：

1. 首页接入 `/api/platform/dashboard`。
2. 增加 API/Web/App/性能统计卡片。
3. 增加测试趋势图和类型分布。
4. 增加最近执行列表。
5. 右侧展示 QualityPilot 的差异化：MCP、RAG、pytest、Allure、AI 失败分析。

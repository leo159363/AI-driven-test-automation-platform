# Stage 11：前端体验重做

## 一、为什么重做

原来的前端主要是把后端接口展示出来，功能能用，但不像一个测试平台：

- 左侧菜单层级不清晰。
- 顶部缺少项目选择、搜索和平台状态。
- 第一次打开没有新手引导。
- API 测试页把很多 JSON 输入框直接堆在一起，不像 Postman / Apifox / FullScopeTest 那样有工作台结构。

## 二、本阶段改了什么

### 1. 全局布局

重做为更接近测试平台的浅色工作台：

- 左侧浅色导航。
- 按模块分组：平台、测试工作台、执行与报告、AI 与知识库。
- 顶部栏增加项目选择、搜索框、能力标签和用户标识。
- 增加新手引导弹窗，第一次打开会提示项目演示顺序。

### 2. API 测试页

API 测试页改成更接近真实接口测试工具的工作台：

- 左侧接口目录。
- 中间接口列表。
- 右侧请求工作台。
- 请求工作台包含：
  - 请求名称
  - method / path
  - 环境选择
  - Base URL
  - Body Type
  - Params
  - Headers
  - Body
  - 断言
  - Mock
  - 用例说明

并保留：

- 发送请求
- AI 裂变用例
- 导出 cURL
- 响应与断言结果
- 接口详情
- AI 编排预览

## 三、和 FullScopeTest 的关系

本阶段参考 FullScopeTest 的产品结构和交互习惯：

- 首页新手引导。
- 浅色侧边栏。
- 工作台式布局。
- API 测试页使用 Params / Headers / Body / Mock 这种标签页结构。

但没有复制它的代码。QualityPilot 仍然保留自己的定位：

- Vue + FastAPI。
- pytest / Allure 自动化执行闭环。
- RAG 知识库。
- MCP tools。
- AI 用例生成、失败分析和 Bug 报告。

## 四、验证

已执行：

```powershell
cd frontend\qualitypilot-web
npm.cmd run build
```

构建通过。

## 五、下一阶段

下一阶段应该继续补：

- API 用例新增、保存、删除。
- 环境配置管理页面。
- Web 测试工作台。
- 性能测试场景页面。
- 首页图表和最近执行数据。

<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  getApiEndpoints,
  getAutomationScenarios,
  getHealth,
  getLatestReport,
  getTestCases,
} from "../services/api";
import type {
  ApiEndpointResponse,
  AutomationScenarioResponse,
  HealthResponse,
  LatestReportResponse,
  TestCaseCatalogResponse,
} from "../types";

const health = ref<HealthResponse | null>(null);
const cases = ref<TestCaseCatalogResponse | null>(null);
const endpoints = ref<ApiEndpointResponse | null>(null);
const scenarios = ref<AutomationScenarioResponse | null>(null);
const reports = ref<LatestReportResponse | null>(null);
const error = ref("");

const demoSteps = [
  {
    index: "01",
    title: "API 测试中心",
    path: "/api-testing",
    action: "先点这里",
    detail: "选择登录接口，直接点击发送请求，看状态码、JSON 字段断言、响应耗时和 cURL。",
  },
  {
    index: "02",
    title: "AI 裂变用例",
    path: "/api-testing",
    action: "生成用例",
    detail: "在 API 测试页点击 AI 裂变用例，生成正常、异常、边界和安全类接口用例。",
  },
  {
    index: "03",
    title: "自动化执行",
    path: "/automation",
    action: "运行 pytest",
    detail: "选择 api_login 或 api_file_upload，触发后端 pytest 执行并生成测试产物。",
  },
  {
    index: "04",
    title: "测试报告",
    path: "/reports",
    action: "看报告",
    detail: "查看 JUnit XML、Allure results、执行状态、通过数和失败数。",
  },
  {
    index: "05",
    title: "知识库管理",
    path: "/knowledge",
    action: "检索上下文",
    detail: "输入 login token 401，查看 RAG 召回的需求、接口文档、规范或历史缺陷片段。",
  },
  {
    index: "06",
    title: "AI 测试助手",
    path: "/assistant",
    action: "生成产物",
    detail: "选择用例生成、失败分析或 Bug 报告模板，让 AI 输出结构化测试产物。",
  },
];

onMounted(async () => {
  try {
    const [healthData, caseData, endpointData, scenarioData, reportData] = await Promise.all([
      getHealth(),
      getTestCases(),
      getApiEndpoints(),
      getAutomationScenarios(),
      getLatestReport(),
    ]);
    health.value = healthData;
    cases.value = caseData;
    endpoints.value = endpointData;
    scenarios.value = scenarioData;
    reports.value = reportData;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>平台总览</h2>
        <p>从 FastAPI 后端读取核心测试资产，作为 Vue 全栈改造的第一屏。</p>
      </div>
      <span v-if="health" class="status-pill ok">API {{ health.status }}</span>
      <span v-else class="status-pill warn">等待后端</span>
    </div>

    <div v-if="error" class="error-banner">
      无法连接 FastAPI：{{ error }}。建议在项目根目录运行
      <span class="path-text">.\.venv\Scripts\python.exe scripts\start_fullstack.py</span>
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span>测试用例</span>
        <strong>{{ cases?.summary.total ?? "--" }}</strong>
      </div>
      <div class="metric-card">
        <span>API 接口</span>
        <strong>{{ endpoints?.summary.total ?? "--" }}</strong>
      </div>
      <div class="metric-card">
        <span>自动化场景</span>
        <strong>{{ scenarios?.summary.total ?? "--" }}</strong>
      </div>
      <div class="metric-card">
        <span>报告产物</span>
        <strong>{{ reports?.artifacts.filter((item) => item.exists).length ?? "--" }}</strong>
      </div>
    </div>

    <div class="panel demo-guide">
      <div class="item-title">
        <div>
          <h3>第一次打开先按这个顺序演示</h3>
          <p class="muted">
            这不是单纯的聊天机器人，也不是只跑一个脚本；它的主线是 API 测试设计、自动化执行、报告解析、RAG 检索和 AI 分析。
          </p>
        </div>
        <span class="status-pill ok">面试演示路线</span>
      </div>
      <div class="demo-step-grid">
        <article v-for="step in demoSteps" :key="step.index" class="demo-step-card">
          <div class="demo-step-header">
            <span class="step-index">{{ step.index }}</span>
            <strong>{{ step.title }}</strong>
          </div>
          <p>{{ step.detail }}</p>
          <RouterLink :to="step.path" class="link-button">{{ step.action }}</RouterLink>
        </article>
      </div>
    </div>

    <div class="two-column section-gap">
      <div class="panel">
        <h3>测试开发闭环</h3>
        <div class="flow-list">
          <div class="flow-step">文档入库</div>
          <div class="flow-step">RAG 检索</div>
          <div class="flow-step">用例生成</div>
          <div class="flow-step">pytest 执行</div>
          <div class="flow-step">Allure 报告</div>
          <div class="flow-step">失败分析</div>
        </div>
      </div>

      <div class="panel">
        <h3>当前后端接口</h3>
        <div class="stack">
          <div class="path-text">GET /api/health</div>
          <div class="path-text">GET /api/test-cases</div>
          <div class="path-text">GET /api/api-endpoints</div>
          <div class="path-text">GET /api/automation/scenarios</div>
          <div class="path-text">GET /api/reports/latest</div>
        </div>
      </div>
    </div>

    <div class="panel section-gap">
      <h3>你现在看到这个项目应该怎么理解</h3>
      <div class="explain-grid">
        <div>
          <strong>它像什么</strong>
          <p class="muted">像一个轻量版测试平台：接口用例、执行入口、报告中心、知识库和 AI 助手放在同一个工作台里。</p>
        </div>
        <div>
          <strong>它测试什么</strong>
          <p class="muted">当前重点是 API 自动化和测试设计闭环，后续可以继续补 Web 自动化、性能测试和用例持久化。</p>
        </div>
        <div>
          <strong>AI 在哪里</strong>
          <p class="muted">AI 不是替你乱点页面，而是辅助生成用例、裂变测试数据、检索知识库、分析失败和生成 Bug 报告。</p>
        </div>
      </div>
    </div>
  </section>
</template>

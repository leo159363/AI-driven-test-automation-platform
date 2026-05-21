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
      无法连接 FastAPI：{{ error }}。请先启动
      <span class="path-text">python -m uvicorn src.api.main:app --reload</span>
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

    <div class="two-column">
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
  </section>
</template>


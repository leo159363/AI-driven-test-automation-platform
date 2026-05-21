<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getApiEndpoints } from "../services/api";
import type { ApiEndpointItem } from "../types";

const endpoints = ref<ApiEndpointItem[]>([]);
const selectedEndpointId = ref("");
const error = ref("");

const selectedEndpoint = computed(
  () => endpoints.value.find((item) => item.endpoint_id === selectedEndpointId.value) ?? endpoints.value[0],
);

const folders = computed(() => {
  const groups = new Map<string, ApiEndpointItem[]>();
  for (const endpoint of endpoints.value) {
    groups.set(endpoint.module, [...(groups.get(endpoint.module) ?? []), endpoint]);
  }
  return Array.from(groups.entries());
});

const selectedRunCommand = computed(() => {
  if (!selectedEndpoint.value) {
    return "";
  }
  return `.\\.venv\\Scripts\\python.exe scripts\\run_automation_suite.py --scenario ${selectedEndpoint.value.scenario_id}`;
});

onMounted(async () => {
  try {
    const data = await getApiEndpoints();
    endpoints.value = data.items;
    selectedEndpointId.value = data.items[0]?.endpoint_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>API 测试中心</h2>
        <p>按接口目录、请求信息、断言、关联用例和自动化场景组织测试资产。</p>
      </div>
      <button class="primary-button" disabled>运行选中接口</button>
    </div>

    <div v-if="error" class="error-banner">接口数据加载失败：{{ error }}</div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span>接口用例</span>
        <strong>{{ endpoints.length }}</strong>
      </div>
      <div class="metric-card">
        <span>接口模块</span>
        <strong>{{ folders.length }}</strong>
      </div>
      <div class="metric-card">
        <span>已自动化</span>
        <strong>{{ endpoints.filter((item) => item.automation_status.includes("已")).length }}</strong>
      </div>
      <div class="metric-card">
        <span>pytest 场景</span>
        <strong>{{ new Set(endpoints.map((item) => item.scenario_id)).size }}</strong>
      </div>
    </div>

    <div class="split-layout">
      <aside class="panel">
        <h3>接口目录</h3>
        <div class="stack">
          <div v-for="[folder, items] in folders" :key="folder" class="api-folder">
            <strong>{{ folder }}</strong>
            <button
              v-for="endpoint in items"
              :key="endpoint.endpoint_id"
              class="tree-button"
              :class="{ active: endpoint.endpoint_id === selectedEndpoint?.endpoint_id }"
              type="button"
              @click="selectedEndpointId = endpoint.endpoint_id"
            >
              <span class="method-mini">{{ endpoint.method }}</span>
              <span>{{ endpoint.name }}</span>
            </button>
          </div>
        </div>
      </aside>

      <div class="panel">
        <h3>接口列表</h3>
        <div class="stack">
          <article
            v-for="endpoint in endpoints"
            :key="endpoint.endpoint_id"
            class="endpoint-card"
            :class="{ selected: endpoint === selectedEndpoint }"
            @click="selectedEndpointId = endpoint.endpoint_id"
          >
            <div class="item-title">
              <strong>{{ endpoint.name }}</strong>
              <span class="method-pill">{{ endpoint.method }}</span>
            </div>
            <p class="path-text">{{ endpoint.path }}</p>
            <p class="muted">{{ endpoint.description }}</p>
            <div>
              <span class="tag">{{ endpoint.module }}</span>
              <span class="tag">{{ endpoint.related_case_id }}</span>
              <span class="tag">{{ endpoint.automation_status }}</span>
            </div>
          </article>
        </div>
      </div>

      <div class="panel">
        <h3>接口详情</h3>
        <template v-if="selectedEndpoint">
          <div class="item-title">
            <strong>{{ selectedEndpoint.name }}</strong>
            <span class="method-pill">{{ selectedEndpoint.method }}</span>
          </div>
          <p class="path-text">{{ selectedEndpoint.path }}</p>
          <p class="muted">{{ selectedEndpoint.description }}</p>

          <h3>Headers</h3>
          <table class="data-table compact-table">
            <tbody>
              <tr v-for="[key, value] in Object.entries(selectedEndpoint.headers)" :key="key">
                <td class="path-text">{{ key }}</td>
                <td>{{ value }}</td>
              </tr>
            </tbody>
          </table>

          <h3>Request Body</h3>
          <pre class="code-block">{{ selectedEndpoint.request_body }}</pre>

          <h3>Assertions</h3>
          <ul class="assertion-list">
            <li v-for="assertion in selectedEndpoint.assertions" :key="assertion">{{ assertion }}</li>
          </ul>

          <h3>关联测试用例</h3>
          <span class="tag">{{ selectedEndpoint.related_case_id }}</span>

          <h3>pytest 自动化</h3>
          <p class="path-text">{{ selectedEndpoint.pytest_target }}</p>
          <pre class="code-block">{{ selectedRunCommand }}</pre>
          <div class="toolbar">
            <span class="status-pill ok">{{ selectedEndpoint.automation_status }}</span>
            <span class="status-pill warn">Stage 4 接入页面运行</span>
          </div>
        </template>
        <div v-else class="empty-state">暂无接口数据</div>
      </div>
    </div>
  </section>
</template>

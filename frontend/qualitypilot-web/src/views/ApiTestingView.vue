<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getApiEndpoints, sendApiDebugRequest } from "../services/api";
import type { ApiDebugResponse, ApiEndpointItem } from "../types";

interface JsonAssertionEditor {
  path: string;
  operator: string;
  expected: string;
}

const endpoints = ref<ApiEndpointItem[]>([]);
const selectedEndpointId = ref("");
const error = ref("");
const loading = ref(false);
const debugResponse = ref<ApiDebugResponse | null>(null);

const targetBaseUrl = ref("");
const headersEditor = ref("{}");
const bodyEditor = ref("");
const expectedStatus = ref<number | null>(200);
const jsonAssertions = ref<JsonAssertionEditor[]>([]);

const selectedEndpoint = computed<ApiEndpointItem | undefined>(
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

const responsePreview = computed(() => {
  if (!debugResponse.value) {
    return "";
  }
  return debugResponse.value.response.json
    ? JSON.stringify(debugResponse.value.response.json, null, 2)
    : debugResponse.value.response.body;
});

function selectEndpoint(endpointId: string): void {
  selectedEndpointId.value = endpointId;
  debugResponse.value = null;
}

function syncEditor(endpoint: ApiEndpointItem | undefined): void {
  if (!endpoint) {
    return;
  }
  headersEditor.value = JSON.stringify(endpoint.headers, null, 2);
  bodyEditor.value = endpoint.request_body.startsWith("<binary")
    ? "demo-binary-content"
    : endpoint.request_body;
  const defaults = buildDefaultAssertions(endpoint.endpoint_id);
  expectedStatus.value = defaults.expectedStatus;
  jsonAssertions.value = defaults.jsonAssertions;
}

function buildDefaultAssertions(endpointId: string): {
  expectedStatus: number;
  jsonAssertions: JsonAssertionEditor[];
} {
  if (endpointId.includes("invalid-password")) {
    return {
      expectedStatus: 401,
      jsonAssertions: [{ path: "error", operator: "equals", expected: "invalid_credentials" }],
    };
  }
  if (endpointId.includes("upload-missing")) {
    return {
      expectedStatus: 400,
      jsonAssertions: [{ path: "error", operator: "equals", expected: "missing_filename" }],
    };
  }
  if (endpointId.includes("upload-success")) {
    return {
      expectedStatus: 201,
      jsonAssertions: [
        { path: "filename", operator: "equals", expected: "demo.txt" },
        { path: "size", operator: "exists", expected: "" },
      ],
    };
  }
  return {
    expectedStatus: 200,
    jsonAssertions: [
      { path: "token", operator: "exists", expected: "" },
      { path: "user.username", operator: "equals", expected: "tester" },
    ],
  };
}

function parseHeaders(): Record<string, string> {
  const parsed = JSON.parse(headersEditor.value || "{}") as unknown;
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Headers 必须是 JSON 对象");
  }
  return Object.fromEntries(
    Object.entries(parsed).map(([key, value]) => [key, String(value)]),
  );
}

function addAssertion(): void {
  jsonAssertions.value.push({ path: "error", operator: "exists", expected: "" });
}

function removeAssertion(index: number): void {
  jsonAssertions.value.splice(index, 1);
}

async function submitDebugRequest(): Promise<void> {
  if (!selectedEndpoint.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    debugResponse.value = await sendApiDebugRequest({
      method: selectedEndpoint.value.method,
      path: selectedEndpoint.value.path,
      base_url: targetBaseUrl.value,
      headers: parseHeaders(),
      body: bodyEditor.value,
      expected_status: expectedStatus.value,
      json_assertions: jsonAssertions.value.filter((item) => item.path.trim()),
      timeout_seconds: 10,
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

watch(selectedEndpoint, (endpoint) => syncEditor(endpoint), { immediate: true });

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
        <p>按接口目录、请求信息、断言、关联用例和自动化场景组织测试资产，并支持受控接口调试。</p>
      </div>
      <button class="primary-button" :disabled="loading || !selectedEndpoint" @click="submitDebugRequest">
        {{ loading ? "发送中..." : "发送选中接口" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">接口调试失败：{{ error }}</div>

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
        <span>调试模式</span>
        <strong>{{ targetBaseUrl ? "HTTP" : "Mock" }}</strong>
      </div>
    </div>

    <div class="api-testing-layout">
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
              @click="selectEndpoint(endpoint.endpoint_id)"
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
            @click="selectEndpoint(endpoint.endpoint_id)"
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
        <h3>请求调试器</h3>
        <template v-if="selectedEndpoint">
          <div class="api-request-line">
            <span class="method-pill">{{ selectedEndpoint.method }}</span>
            <span class="path-text">{{ selectedEndpoint.path }}</span>
          </div>

          <label>
            目标 Base URL
            <input
              v-model="targetBaseUrl"
              class="form-control"
              placeholder="留空使用内置 Mock；例如 http://127.0.0.1:9000"
            />
          </label>

          <label>
            Headers JSON
            <textarea v-model="headersEditor" class="assistant-textarea compact-textarea code-editor" rows="5" />
          </label>

          <label>
            Request Body
            <textarea v-model="bodyEditor" class="assistant-textarea compact-textarea code-editor" rows="6" />
          </label>

          <div class="assertion-editor">
            <div class="item-title">
              <h3>断言配置</h3>
              <button class="ghost-button" type="button" @click="addAssertion">新增 JSON 断言</button>
            </div>
            <label>
              期望状态码
              <input v-model.number="expectedStatus" class="small-input" type="number" />
            </label>
            <div
              v-for="(assertion, index) in jsonAssertions"
              :key="`${assertion.path}-${index}`"
              class="assertion-row"
            >
              <input v-model="assertion.path" class="form-control" placeholder="JSON Path，例如 token" />
              <select v-model="assertion.operator" class="form-control">
                <option value="equals">equals</option>
                <option value="contains">contains</option>
                <option value="exists">exists</option>
                <option value="not_exists">not_exists</option>
              </select>
              <input v-model="assertion.expected" class="form-control" placeholder="期望值" />
              <button class="ghost-button" type="button" @click="removeAssertion(index)">删除</button>
            </div>
          </div>

          <button class="primary-button full-width" :disabled="loading" @click="submitDebugRequest">
            {{ loading ? "发送中..." : "发送请求并执行断言" }}
          </button>
        </template>
        <div v-else class="empty-state">暂无接口数据</div>
      </div>
    </div>

    <div class="two-column api-debug-section">
      <div class="panel">
        <h3>接口详情</h3>
        <template v-if="selectedEndpoint">
          <div class="item-title">
            <strong>{{ selectedEndpoint.name }}</strong>
            <span class="method-pill">{{ selectedEndpoint.method }}</span>
          </div>
          <p class="path-text">{{ selectedEndpoint.path }}</p>
          <p class="muted">{{ selectedEndpoint.description }}</p>

          <h3>Assertions</h3>
          <ul class="assertion-list">
            <li v-for="assertion in selectedEndpoint.assertions" :key="assertion">{{ assertion }}</li>
          </ul>

          <h3>关联测试用例</h3>
          <span class="tag">{{ selectedEndpoint.related_case_id }}</span>

          <h3>pytest 自动化</h3>
          <p class="path-text">{{ selectedEndpoint.pytest_target }}</p>
          <pre class="code-block">{{ selectedRunCommand }}</pre>
        </template>
      </div>

      <div class="panel">
        <div class="item-title">
          <h3>响应与断言结果</h3>
          <span v-if="debugResponse" class="status-pill" :class="debugResponse.passed ? 'ok' : 'warn'">
            {{ debugResponse.passed ? "通过" : "失败" }}
          </span>
        </div>
        <template v-if="debugResponse">
          <div class="toolbar">
            <span class="tag">status {{ debugResponse.response.status_code }}</span>
            <span class="tag">{{ debugResponse.response.duration_ms }} ms</span>
            <span class="tag">{{ debugResponse.request.target_mode }}</span>
            <span class="tag">
              assert {{ debugResponse.summary.passed }}/{{ debugResponse.summary.total }}
            </span>
          </div>
          <table class="data-table compact-table assertion-result-table">
            <tbody>
              <tr v-for="assertion in debugResponse.assertions" :key="assertion.name">
                <td>
                  <span class="status-pill" :class="assertion.passed ? 'ok' : 'warn'">
                    {{ assertion.passed ? "PASS" : "FAIL" }}
                  </span>
                </td>
                <td>{{ assertion.name }}</td>
                <td class="path-text">actual: {{ assertion.actual }}</td>
              </tr>
            </tbody>
          </table>
          <h3>Response Body</h3>
          <pre class="code-block">{{ responsePreview }}</pre>
        </template>
        <div v-else class="empty-state">点击发送请求后，这里会展示响应体、耗时和断言结果。</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  exportApiCurl,
  getApiCollections,
  getApiEndpoints,
  getApiTestingEnvironments,
  planApiOperations,
  runApiCollection,
  saveApiCase,
  sendApiDebugRequest,
  synthesizeApiCases,
} from "../services/api";
import type {
  ApiCollection,
  ApiDebugResponse,
  ApiEndpointItem,
  ApiEnvironment,
  ApiOperationPlanResponse,
  ApiSynthesizedCase,
  PlatformRunRecord,
} from "../types";

interface JsonAssertionEditor {
  path: string;
  operator: string;
  expected: string;
}

interface FieldGuide {
  field: string;
  fill: string;
  why: string;
}

interface EndpointGuide {
  goal: string;
  fields: FieldGuide[];
  expected: string;
}

type RequestTab = "params" | "headers" | "body" | "pre_script" | "post_script" | "mock" | "guide";
type SidebarTab = "cases" | "collections";

const endpoints = ref<ApiEndpointItem[]>([]);
const environments = ref<ApiEnvironment[]>([]);
const collections = ref<ApiCollection[]>([]);
const selectedEndpointId = ref("");
const selectedEnvironmentId = ref("mock-local");
const moduleFilter = ref("all");
const searchKeyword = ref("");
const sidebarTab = ref<SidebarTab>("cases");
const error = ref("");
const loading = ref(false);
const debugResponse = ref<ApiDebugResponse | null>(null);
const requestFeedback = ref("当前默认使用内置 Mock 环境，直接点击发送请求即可看到响应和断言。");
const requestFeedbackType = ref<"info" | "success" | "error">("info");

const targetBaseUrl = ref("");
const headersEditor = ref("{}");
const paramsEditor = ref("{}");
const variablesEditor = ref("{}");
const environmentHeadersEditor = ref("{}");
const bodyEditor = ref("");
const preScriptEditor = ref("// 前置脚本示例：可以在这里准备 token、环境变量或动态参数。");
const postScriptEditor = ref("// 后置断言示例：检查响应 schema、提取字段、写入变量。");
const bodyType = ref("json");
const expectedStatus = ref<number | null>(200);
const jsonAssertions = ref<JsonAssertionEditor[]>([]);

const mockEnabled = ref(false);
const mockStatusCode = ref(200);
const mockDelayMs = ref(0);
const mockBody = ref('{"message": "mock response"}');

const synthesizedCases = ref<ApiSynthesizedCase[]>([]);
const planPrompt = ref("帮我为登录接口创建测试集合，生成正常登录和异常登录用例，并执行集合。");
const operationPlan = ref<ApiOperationPlanResponse | null>(null);
const collectionRun = ref<PlatformRunRecord | null>(null);
const curlCommand = ref("");
const activeRequestTab = ref<RequestTab>("body");

const requestTabs: Array<{ id: RequestTab; label: string }> = [
  { id: "params", label: "Params" },
  { id: "headers", label: "Headers" },
  { id: "body", label: "Body" },
  { id: "pre_script", label: "前置脚本" },
  { id: "post_script", label: "断言脚本" },
  { id: "mock", label: "Mock" },
  { id: "guide", label: "说明" },
];

const endpointGuides: Record<string, EndpointGuide> = {
  "api-login-success": {
    goal: "验证登录主流程：账号 tester 和密码 Passw0rd! 正确时，接口应该返回 token。",
    expected: "HTTP 200，响应体包含 token，并且 user.username 等于 tester。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "不需要真实后端服务，适合本地演示。" },
      { field: "Base URL", fill: "留空", why: "留空会走平台内置的 mock 登录接口。" },
      { field: "Request Body", fill: '{"username": "tester", "password": "Passw0rd!"}', why: "正确账号密码。" },
      { field: "断言", fill: "状态码 200，token exists，user.username equals tester", why: "验证接口业务结果。" },
    ],
  },
  "api-login-invalid-password": {
    goal: "验证登录异常流：密码错误时，接口不能返回 token，应该拒绝登录。",
    expected: "HTTP 401，响应体 error 等于 invalid_credentials。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "稳定演示异常分支。" },
      { field: "Request Body", fill: '{"username": "tester", "password": "wrong"}', why: "故意传错误密码。" },
      { field: "断言", fill: "状态码 401，error equals invalid_credentials", why: "验证鉴权失败处理。" },
    ],
  },
  "api-upload-success": {
    goal: "验证文件上传主流程：传入二进制内容和文件名，接口应该返回文件名和大小。",
    expected: "HTTP 201，响应体 filename 等于 demo.txt，并且 size 存在。",
    fields: [
      { field: "Body Type", fill: "raw", why: "这里模拟二进制文件内容，不是 JSON。" },
      { field: "Headers", fill: '{"Content-Type": "application/octet-stream", "X-Filename": "demo.txt"}', why: "X-Filename 表示上传文件名。" },
      { field: "Request Body", fill: "demo-binary-content", why: "用字符串模拟文件内容。" },
      { field: "断言", fill: "状态码 201，filename equals demo.txt，size exists", why: "验证上传结果。" },
    ],
  },
  "api-upload-missing-filename": {
    goal: "验证文件上传参数校验：缺少文件名 header 时，接口应该返回参数错误。",
    expected: "HTTP 400，响应体 error 等于 missing_filename。",
    fields: [
      { field: "Headers", fill: '{"Content-Type": "application/octet-stream"}', why: "故意不传 X-Filename。" },
      { field: "Request Body", fill: "demo-binary-content", why: "文件内容存在，但文件名缺失。" },
      { field: "断言", fill: "状态码 400，error equals missing_filename", why: "验证参数校验逻辑。" },
    ],
  },
};

const selectedEndpoint = computed<ApiEndpointItem | undefined>(
  () => endpoints.value.find((item) => item.endpoint_id === selectedEndpointId.value) ?? endpoints.value[0],
);

const selectedEnvironment = computed<ApiEnvironment | undefined>(
  () =>
    environments.value.find((item) => item.environment_id === selectedEnvironmentId.value) ??
    environments.value[0],
);

const folders = computed(() => {
  const groups = new Map<string, ApiEndpointItem[]>();
  for (const endpoint of endpoints.value) {
    groups.set(endpoint.module, [...(groups.get(endpoint.module) ?? []), endpoint]);
  }
  return Array.from(groups.entries());
});

const moduleOptions = computed(() => ["all", ...folders.value.map(([folder]) => folder)]);

const filteredEndpoints = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  return endpoints.value.filter((endpoint) => {
    const moduleMatched = moduleFilter.value === "all" || endpoint.module === moduleFilter.value;
    const keywordMatched =
      !keyword ||
      `${endpoint.name} ${endpoint.path} ${endpoint.module} ${endpoint.related_case_id}`
        .toLowerCase()
        .includes(keyword);
    return moduleMatched && keywordMatched;
  });
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

const selectedEndpointGuide = computed<EndpointGuide | undefined>(() => {
  const endpointId = selectedEndpoint.value?.endpoint_id;
  return endpointId ? endpointGuides[endpointId] : undefined;
});

const isLocalHttpMode = computed(() => Boolean(targetBaseUrl.value.trim()));

const activeCollection = computed<ApiCollection | undefined>(() => {
  if (!selectedEndpoint.value) {
    return collections.value[0];
  }
  const collectionId = selectedEndpoint.value.module.includes("上传") ? "upload" : "auth";
  return collections.value.find((item) => item.collection_id === collectionId) ?? collections.value[0];
});

function selectEndpoint(endpointId: string): void {
  selectedEndpointId.value = endpointId;
  debugResponse.value = null;
  synthesizedCases.value = [];
  curlCommand.value = "";
  mockEnabled.value = false;
  activeRequestTab.value = "body";
  switchToMockEnvironment();
}

function resetCurrentExample(): void {
  syncEditor(selectedEndpoint.value);
  switchToMockEnvironment();
  mockEnabled.value = false;
  curlCommand.value = "";
  debugResponse.value = null;
  requestFeedback.value = "已恢复当前用例的默认请求数据，并切回内置 Mock 环境。";
  requestFeedbackType.value = "info";
}

function switchToMockEnvironment(): void {
  selectedEnvironmentId.value = "mock-local";
  const mockEnvironment = environments.value.find((item) => item.environment_id === "mock-local");
  if (mockEnvironment) {
    syncEnvironment(mockEnvironment);
  } else {
    targetBaseUrl.value = "";
  }
}

function syncEditor(endpoint: ApiEndpointItem | undefined): void {
  if (!endpoint) {
    return;
  }
  headersEditor.value = JSON.stringify(endpoint.headers, null, 2);
  paramsEditor.value = "{}";
  preScriptEditor.value = "// 当前演示没有真实前置脚本。面试时可以说明这里可做登录 token 提取、变量初始化。";
  postScriptEditor.value = "// 当前断言由右侧 JSON 断言表驱动。后续可扩展为 JS 脚本断言。";
  bodyEditor.value = endpoint.request_body.startsWith("<binary")
    ? "demo-binary-content"
    : endpoint.request_body;
  bodyType.value = endpoint.request_body.startsWith("<binary") ? "raw" : "json";
  const defaults = buildDefaultAssertions(endpoint.endpoint_id);
  expectedStatus.value = defaults.expectedStatus;
  jsonAssertions.value = defaults.jsonAssertions;
}

function syncEnvironment(environment: ApiEnvironment | undefined): void {
  if (!environment) {
    return;
  }
  targetBaseUrl.value = environment.base_url;
  variablesEditor.value = JSON.stringify(environment.variables, null, 2);
  environmentHeadersEditor.value = JSON.stringify(environment.headers, null, 2);
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

function parseJsonObject(text: string, label: string): Record<string, string> {
  const parsed = JSON.parse(text || "{}") as unknown;
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} 必须是 JSON 对象`);
  }
  return Object.fromEntries(Object.entries(parsed).map(([key, value]) => [key, String(value)]));
}

function currentEnvironmentPayload(): Partial<ApiEnvironment> {
  const environment = selectedEnvironment.value;
  return {
    environment_id: environment?.environment_id ?? "",
    name: environment?.name ?? "",
    description: environment?.description ?? "",
    base_url: targetBaseUrl.value,
    variables: parseJsonObject(variablesEditor.value, "环境变量"),
    headers: parseJsonObject(environmentHeadersEditor.value, "环境公共 Headers"),
  };
}

function buildRequestPayload(): Parameters<typeof sendApiDebugRequest>[0] {
  if (!selectedEndpoint.value) {
    throw new Error("请先选择接口");
  }
  return {
    method: selectedEndpoint.value.method,
    path: selectedEndpoint.value.path,
    base_url: targetBaseUrl.value,
    headers: parseJsonObject(headersEditor.value, "Headers"),
    params: parseJsonObject(paramsEditor.value, "Query Params"),
    body: bodyEditor.value,
    body_type: bodyType.value,
    environment: currentEnvironmentPayload(),
    mock_config: {
      enabled: mockEnabled.value,
      status_code: mockStatusCode.value,
      delay_ms: mockDelayMs.value,
      headers: { "Content-Type": "application/json" },
      body: mockBody.value,
    },
    expected_status: expectedStatus.value,
    json_assertions: jsonAssertions.value.filter((item) => item.path.trim()),
    timeout_seconds: 10,
  };
}

function addAssertion(): void {
  jsonAssertions.value.push({ path: "error", operator: "exists", expected: "" });
}

function removeAssertion(index: number): void {
  jsonAssertions.value.splice(index, 1);
}

function applySynthesizedCase(testCase: ApiSynthesizedCase): void {
  headersEditor.value = JSON.stringify(testCase.headers, null, 2);
  bodyEditor.value = testCase.body;
  expectedStatus.value = testCase.expected_status;
  jsonAssertions.value = testCase.json_assertions.map((item) => ({
    path: item.path,
    operator: item.operator,
    expected: item.expected ?? "",
  }));
  activeRequestTab.value = "post_script";
}

async function submitDebugRequest(): Promise<void> {
  loading.value = true;
  error.value = "";
  debugResponse.value = null;
  requestFeedback.value = "请求发送中，请等待响应结果。";
  requestFeedbackType.value = "info";
  try {
    debugResponse.value = await sendApiDebugRequest(buildRequestPayload());
    if (debugResponse.value.request.target_mode === "local_http_error") {
      requestFeedback.value = "本机 API 连接失败。演示时请点击“切回内置 Mock”，然后重新发送。";
      requestFeedbackType.value = "error";
    } else if (debugResponse.value.passed) {
      requestFeedback.value = "请求已完成，断言通过。下面可以查看响应体、耗时和断言结果。";
      requestFeedbackType.value = "success";
    } else {
      requestFeedback.value = "请求已完成，但断言未通过。请查看下方响应与断言结果。";
      requestFeedbackType.value = "error";
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    requestFeedback.value = "请求没有成功发出，请查看页面上方错误信息。";
    requestFeedbackType.value = "error";
  } finally {
    loading.value = false;
  }
}

async function submitSynthesize(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const payload = buildRequestPayload();
    const data = await synthesizeApiCases({
      method: payload.method,
      path: payload.path,
      headers: payload.headers,
      body: payload.body,
      count: 6,
    });
    synthesizedCases.value = data.cases;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitPlan(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    operationPlan.value = await planApiOperations({
      prompt: planPrompt.value,
      context: {
        selected_endpoint_id: selectedEndpoint.value?.endpoint_id,
        selected_environment_id: selectedEnvironment.value?.environment_id,
      },
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitCurlExport(): Promise<void> {
  error.value = "";
  try {
    const data = await exportApiCurl(buildRequestPayload());
    curlCommand.value = data.curl;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function submitSaveCase(): Promise<void> {
  if (!selectedEndpoint.value) {
    return;
  }
  error.value = "";
  try {
    const payload = buildRequestPayload();
    const result = await saveApiCase({
      name: selectedEndpoint.value.name,
      method: payload.method,
      path: payload.path,
      collection_id: activeCollection.value?.collection_id ?? "auth",
      headers: payload.headers,
      body: payload.body,
      expected_status: payload.expected_status,
      json_assertions: payload.json_assertions,
    });
    requestFeedback.value = result.message;
    requestFeedbackType.value = "success";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function submitRunCollection(collectionId?: string): Promise<void> {
  const targetCollectionId = collectionId ?? activeCollection.value?.collection_id;
  if (!targetCollectionId) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    collectionRun.value = await runApiCollection(targetCollectionId);
    requestFeedback.value = `集合 ${collectionRun.value.name} 已执行：${collectionRun.value.summary.passed}/${collectionRun.value.summary.total} 通过。`;
    requestFeedbackType.value = "success";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

watch(selectedEndpoint, (endpoint) => syncEditor(endpoint), { immediate: true });
watch(selectedEnvironment, (environment) => syncEnvironment(environment), { immediate: true });

onMounted(async () => {
  try {
    const [endpointData, environmentData, collectionData] = await Promise.all([
      getApiEndpoints(),
      getApiTestingEnvironments(),
      getApiCollections(),
    ]);
    endpoints.value = endpointData.items;
    environments.value = environmentData.items;
    collections.value = collectionData.items;
    selectedEndpointId.value = endpointData.items[0]?.endpoint_id ?? "";
    moduleFilter.value = endpointData.summary.modules[0] ?? "all";
    switchToMockEnvironment();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section class="fst-api-page">
    <div v-if="error" class="error-banner">接口工作台错误：{{ error }}</div>

    <div class="fst-api-workspace">
      <aside class="fst-api-sidebar">
        <div class="side-tabs">
          <button
            class="side-tab"
            :class="{ active: sidebarTab === 'cases' }"
            type="button"
            @click="sidebarTab = 'cases'"
          >
            测试用例
          </button>
          <button
            class="side-tab"
            :class="{ active: sidebarTab === 'collections' }"
            type="button"
            @click="sidebarTab = 'collections'"
          >
            集合管理
          </button>
        </div>

        <div class="fst-sidebar-tools">
          <input v-model="searchKeyword" class="form-control" placeholder="搜索用例..." />
          <button class="ghost-button icon-only" type="button" @click="resetCurrentExample">↻</button>
        </div>

        <select v-model="moduleFilter" class="form-control">
          <option v-for="item in moduleOptions" :key="item" :value="item">
            {{ item === "all" ? "全部模块" : item }}
          </option>
        </select>

        <div v-if="sidebarTab === 'cases'" class="fst-case-tree">
          <div v-for="[folder, items] in folders" :key="folder" class="fst-case-folder">
            <strong>▾ {{ folder }}</strong>
            <button
              v-for="endpoint in items.filter((item) => filteredEndpoints.includes(item))"
              :key="endpoint.endpoint_id"
              class="fst-case-item"
              :class="{ active: endpoint.endpoint_id === selectedEndpoint?.endpoint_id }"
              type="button"
              @click="selectEndpoint(endpoint.endpoint_id)"
            >
              <span class="method-mini">{{ endpoint.method }}</span>
              <span>{{ endpoint.name }}</span>
            </button>
          </div>
        </div>

        <div v-else class="stack">
          <article v-for="collection in collections" :key="collection.collection_id" class="context-card">
            <div class="item-title">
              <strong>{{ collection.name }}</strong>
              <span class="tag">{{ collection.case_ids.length }} cases</span>
            </div>
            <p class="muted">{{ collection.description }}</p>
            <button class="ghost-button" type="button" @click="submitRunCollection(collection.collection_id)">
              运行集合
            </button>
          </article>
        </div>
      </aside>

      <main class="fst-request-console">
        <template v-if="selectedEndpoint">
          <div class="fst-request-toolbar">
            <input class="form-control request-name-input" :value="selectedEndpoint.name" readonly />
            <span class="toggle-row">
              <input type="checkbox" checked disabled />
              自动保存草稿
            </span>
            <button class="ghost-button" type="button" @click="resetCurrentExample">新建用例</button>
            <button class="ghost-button" type="button" @click="submitSaveCase">保存</button>
            <button class="ghost-button" type="button" @click="submitSynthesize">AI 扩充用例</button>
            <button class="ghost-button" type="button" @click="submitRunCollection()">运行集合</button>
          </div>

          <div class="fst-url-row">
            <select class="method-select" :value="selectedEndpoint.method" disabled>
              <option>{{ selectedEndpoint.method }}</option>
            </select>
            <input class="form-control request-path-input" :value="selectedEndpoint.path" readonly />
            <button class="primary-button" :disabled="loading" @click="submitDebugRequest">
              {{ loading ? "发送中..." : "发送" }}
            </button>
          </div>

          <div class="fst-env-row">
            <span>环境:</span>
            <select v-model="selectedEnvironmentId" class="form-control">
              <option
                v-for="environment in environments"
                :key="environment.environment_id"
                :value="environment.environment_id"
              >
                {{ environment.name }}
              </option>
            </select>
            <input v-model="targetBaseUrl" class="form-control" placeholder="Base URL 留空使用内置 Mock" />
            <select v-model="bodyType" class="form-control compact-select">
              <option value="json">json</option>
              <option value="raw">raw</option>
              <option value="form">form</option>
            </select>
            <button v-if="isLocalHttpMode" class="ghost-button" type="button" @click="switchToMockEnvironment">
              切回内置 Mock
            </button>
          </div>

          <div
            class="request-feedback"
            :class="{
              success: requestFeedbackType === 'success',
              error: requestFeedbackType === 'error',
            }"
          >
            {{ requestFeedback }}
          </div>

          <div class="request-tabs">
            <button
              v-for="tab in requestTabs"
              :key="tab.id"
              class="request-tab"
              :class="{ active: activeRequestTab === tab.id }"
              type="button"
              @click="activeRequestTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>

          <div class="fst-editor-area">
            <div v-if="activeRequestTab === 'params'" class="tab-panel">
              <label>
                Query Params JSON
                <textarea v-model="paramsEditor" class="assistant-textarea compact-textarea code-editor" rows="8" />
              </label>
            </div>

            <div v-else-if="activeRequestTab === 'headers'" class="tab-panel">
              <div class="two-column compact-editor-grid">
                <label>
                  环境公共 Headers JSON
                  <textarea v-model="environmentHeadersEditor" class="assistant-textarea compact-textarea code-editor" rows="8" />
                </label>
                <label>
                  请求 Headers JSON
                  <textarea v-model="headersEditor" class="assistant-textarea compact-textarea code-editor" rows="8" />
                </label>
              </div>
            </div>

            <div v-else-if="activeRequestTab === 'body'" class="tab-panel">
              <label>
                环境变量 JSON
                <textarea v-model="variablesEditor" class="assistant-textarea compact-textarea code-editor" rows="5" />
              </label>
              <label>
                Request Body
                <textarea v-model="bodyEditor" class="assistant-textarea compact-textarea code-editor" rows="9" />
              </label>
            </div>

            <div v-else-if="activeRequestTab === 'pre_script'" class="tab-panel">
              <label>
                前置脚本
                <textarea v-model="preScriptEditor" class="assistant-textarea compact-textarea code-editor" rows="12" />
              </label>
            </div>

            <div v-else-if="activeRequestTab === 'post_script'" class="tab-panel assertion-editor">
              <div class="item-title">
                <h3>断言脚本 / JSON 断言</h3>
                <button class="ghost-button" type="button" @click="addAssertion">新增 JSON 断言</button>
              </div>
              <textarea v-model="postScriptEditor" class="assistant-textarea compact-textarea code-editor" rows="5" />
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

            <div v-else-if="activeRequestTab === 'mock'" class="tab-panel">
              <div class="mock-row">
                <label class="toggle-row">
                  <input v-model="mockEnabled" type="checkbox" />
                  启用自定义 Mock 响应
                </label>
                <label>
                  状态码
                  <input v-model.number="mockStatusCode" class="small-input" type="number" />
                </label>
                <label>
                  延迟(ms)
                  <input v-model.number="mockDelayMs" class="small-input" type="number" />
                </label>
              </div>
              <textarea v-model="mockBody" class="assistant-textarea compact-textarea code-editor" rows="9" />
            </div>

            <div v-else class="tab-panel">
              <div v-if="selectedEndpointGuide" class="endpoint-guide-card">
                <div class="item-title">
                  <div>
                    <strong>当前用例在测什么</strong>
                    <p>{{ selectedEndpointGuide.goal }}</p>
                  </div>
                  <span class="status-pill ok">示例已填好</span>
                </div>
                <table class="data-table compact-table guide-table">
                  <tbody>
                    <tr v-for="item in selectedEndpointGuide.fields" :key="item.field">
                      <td><strong>{{ item.field }}</strong></td>
                      <td class="path-text">{{ item.fill }}</td>
                      <td>{{ item.why }}</td>
                    </tr>
                  </tbody>
                </table>
                <p class="expected-text"><strong>预期结果：</strong>{{ selectedEndpointGuide.expected }}</p>
              </div>
            </div>
          </div>

          <section class="fst-response-panel">
            <div class="item-title">
              <h3>响应</h3>
              <div class="toolbar" v-if="debugResponse">
                <span class="status-pill" :class="debugResponse.passed ? 'ok' : 'warn'">
                  {{ debugResponse.passed ? "通过" : "失败" }}
                </span>
                <span class="tag">status {{ debugResponse.response.status_code }}</span>
                <span class="tag">{{ debugResponse.response.duration_ms }} ms</span>
                <span class="tag">assert {{ debugResponse.summary.passed }}/{{ debugResponse.summary.total }}</span>
              </div>
            </div>
            <template v-if="debugResponse">
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
              <pre class="code-block">{{ responsePreview }}</pre>
            </template>
            <div v-else class="empty-state">发送请求查看响应</div>
          </section>

          <section class="fst-lower-grid">
            <div class="panel-lite">
              <div class="item-title">
                <h3>AI 扩充用例</h3>
                <span class="tag">{{ synthesizedCases.length }} cases</span>
              </div>
              <div v-if="synthesizedCases.length" class="stack">
                <article v-for="testCase in synthesizedCases" :key="testCase.name" class="endpoint-card">
                  <div class="item-title">
                    <strong>{{ testCase.name }}</strong>
                    <span class="tag">expect {{ testCase.expected_status }}</span>
                  </div>
                  <pre class="mini-code">{{ testCase.body }}</pre>
                  <button class="ghost-button" type="button" @click="applySynthesizedCase(testCase)">
                    应用到调试器
                  </button>
                </article>
              </div>
              <div v-else class="empty-state">点击 AI 扩充用例，生成边界、异常、安全类接口用例。</div>
            </div>

            <div class="panel-lite">
              <div class="item-title">
                <h3>接口详情</h3>
                <button class="ghost-button" type="button" @click="submitCurlExport">导出 cURL</button>
              </div>
              <p class="path-text">{{ selectedEndpoint.method }} {{ selectedEndpoint.path }}</p>
              <p class="muted">{{ selectedEndpoint.description }}</p>
              <span class="tag">{{ selectedEndpoint.related_case_id }}</span>
              <pre class="mini-code">{{ selectedRunCommand }}</pre>
              <pre v-if="curlCommand" class="mini-code">{{ curlCommand }}</pre>
            </div>
          </section>

          <section v-if="collectionRun" class="panel-lite">
            <div class="item-title">
              <h3>集合执行结果</h3>
              <span class="status-pill ok">{{ collectionRun.status }}</span>
            </div>
            <p class="muted">{{ collectionRun.ai_next_step }}</p>
            <div class="toolbar">
              <span class="tag">total {{ collectionRun.summary.total }}</span>
              <span class="tag">passed {{ collectionRun.summary.passed }}</span>
              <span class="tag">failed {{ collectionRun.summary.failed }}</span>
            </div>
            <pre class="mini-code">{{ collectionRun.command }}</pre>
          </section>

          <section class="panel-lite">
            <div class="item-title">
              <h3>AI 编排预览</h3>
              <button class="ghost-button" :disabled="loading" @click="submitPlan">生成计划</button>
            </div>
            <textarea v-model="planPrompt" class="assistant-textarea compact-textarea" rows="4" />
            <template v-if="operationPlan">
              <p class="muted">{{ operationPlan.summary }} / {{ operationPlan.source }}</p>
              <pre class="code-block">{{ JSON.stringify(operationPlan.operations, null, 2) }}</pre>
            </template>
          </section>
        </template>
        <div v-else class="empty-state">暂无接口数据</div>
      </main>
    </div>
  </section>
</template>

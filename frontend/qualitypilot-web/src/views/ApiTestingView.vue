<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  exportApiCurl,
  getApiEndpoints,
  getApiTestingEnvironments,
  planApiOperations,
  sendApiDebugRequest,
  synthesizeApiCases,
} from "../services/api";
import type {
  ApiDebugResponse,
  ApiEndpointItem,
  ApiEnvironment,
  ApiOperationPlanResponse,
  ApiSynthesizedCase,
} from "../types";

interface JsonAssertionEditor {
  path: string;
  operator: string;
  expected: string;
}

interface QuickExample {
  endpointId: string;
  title: string;
  module: string;
  reason: string;
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

type RequestTab = "params" | "headers" | "body" | "assertions" | "mock" | "guide";

const endpoints = ref<ApiEndpointItem[]>([]);
const environments = ref<ApiEnvironment[]>([]);
const selectedEndpointId = ref("");
const selectedEnvironmentId = ref("mock-local");
const error = ref("");
const loading = ref(false);
const debugResponse = ref<ApiDebugResponse | null>(null);
const requestFeedback = ref("当前默认使用内置 Mock 环境，直接点击发送即可。");
const requestFeedbackType = ref<"info" | "success" | "error">("info");

const targetBaseUrl = ref("");
const headersEditor = ref("{}");
const paramsEditor = ref("{}");
const variablesEditor = ref("{}");
const environmentHeadersEditor = ref("{}");
const bodyEditor = ref("");
const bodyType = ref("json");
const expectedStatus = ref<number | null>(200);
const jsonAssertions = ref<JsonAssertionEditor[]>([]);

const mockEnabled = ref(false);
const mockStatusCode = ref(200);
const mockDelayMs = ref(0);
const mockBody = ref('{"message": "mock response"}');

const synthesizedCases = ref<ApiSynthesizedCase[]>([]);
const planPrompt = ref("帮我为登录接口创建测试集合，生成正常登录和异常登录用例，并执行集合");
const operationPlan = ref<ApiOperationPlanResponse | null>(null);
const curlCommand = ref("");
const activeRequestTab = ref<RequestTab>("params");

const requestTabs: Array<{ id: RequestTab; label: string }> = [
  { id: "params", label: "Params" },
  { id: "headers", label: "Headers" },
  { id: "body", label: "Body" },
  { id: "assertions", label: "断言" },
  { id: "mock", label: "Mock" },
  { id: "guide", label: "说明" },
];

const quickExamples: QuickExample[] = [
  {
    endpointId: "api-login-success",
    title: "登录成功",
    module: "登录鉴权",
    reason: "最先跑这个，用正确账号密码验证 token 返回。",
  },
  {
    endpointId: "api-login-invalid-password",
    title: "登录失败",
    module: "登录鉴权",
    reason: "用错误密码验证接口返回 401 和错误码。",
  },
  {
    endpointId: "api-upload-success",
    title: "文件上传成功",
    module: "文件上传",
    reason: "验证带 X-Filename 的二进制上传能返回文件名和大小。",
  },
  {
    endpointId: "api-upload-missing-filename",
    title: "文件上传参数错误",
    module: "文件上传",
    reason: "故意不传 X-Filename，验证参数校验和错误提示。",
  },
];

const endpointGuides: Record<string, EndpointGuide> = {
  "api-login-success": {
    goal: "验证登录主流程：账号 tester 和密码 Passw0rd! 正确时，接口应该返回 token。",
    expected: "HTTP 200，响应体包含 token，并且 user.username 等于 tester。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "不需要真实后端服务，适合本地演示。" },
      { field: "Base URL", fill: "留空", why: "留空会走平台内置的 mock 登录接口。" },
      { field: "环境变量 JSON", fill: '"username": "tester", "password": "Passw0rd!"', why: "这是登录成功用例的数据。" },
      { field: "请求 Headers JSON", fill: '{"Content-Type": "application/json"}', why: "登录接口发送 JSON 请求体。" },
      { field: "Query Params JSON", fill: "{}", why: "这个登录用例不需要 query 参数。" },
      { field: "Request Body", fill: '{"username": "tester", "password": "Passw0rd!"}', why: "正确账号密码。" },
      { field: "断言", fill: "状态码 200，token exists，user.username equals tester", why: "验证接口业务结果。" },
    ],
  },
  "api-login-invalid-password": {
    goal: "验证登录异常流：密码错误时，接口不能返回 token，应该拒绝登录。",
    expected: "HTTP 401，响应体 error 等于 invalid_credentials。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "用内置接口稳定演示异常分支。" },
      { field: "Base URL", fill: "留空", why: "继续使用内置 mock。" },
      { field: "请求 Headers JSON", fill: '{"Content-Type": "application/json"}', why: "登录接口发送 JSON 请求体。" },
      { field: "Request Body", fill: '{"username": "tester", "password": "wrong"}', why: "故意传错误密码。" },
      { field: "断言", fill: "状态码 401，error equals invalid_credentials", why: "验证鉴权失败处理。" },
    ],
  },
  "api-upload-success": {
    goal: "验证文件上传主流程：传入二进制内容和文件名，接口应该返回文件名和大小。",
    expected: "HTTP 201，响应体 filename 等于 demo.txt，并且 size 存在。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "不用准备真实上传服务。" },
      { field: "Body Type", fill: "raw", why: "这里模拟二进制文件内容，不是 JSON。" },
      { field: "请求 Headers JSON", fill: '{"Content-Type": "application/octet-stream", "X-Filename": "demo.txt"}', why: "X-Filename 表示上传文件名。" },
      { field: "Query Params JSON", fill: "{}", why: "上传用例不需要 query 参数。" },
      { field: "Request Body", fill: "demo-binary-content", why: "用字符串模拟文件二进制内容。" },
      { field: "断言", fill: "状态码 201，filename equals demo.txt，size exists", why: "验证上传结果。" },
    ],
  },
  "api-upload-missing-filename": {
    goal: "验证文件上传参数校验：缺少文件名 header 时，接口应该返回参数错误。",
    expected: "HTTP 400，响应体 error 等于 missing_filename。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "稳定演示参数错误分支。" },
      { field: "Body Type", fill: "raw", why: "上传内容仍然是原始文本模拟文件。" },
      { field: "请求 Headers JSON", fill: '{"Content-Type": "application/octet-stream"}', why: "故意不传 X-Filename。" },
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

function selectEndpoint(endpointId: string): void {
  selectedEndpointId.value = endpointId;
  debugResponse.value = null;
  synthesizedCases.value = [];
  curlCommand.value = "";
  mockEnabled.value = false;
  switchToMockEnvironment();
}

function resetCurrentExample(): void {
  syncEditor(selectedEndpoint.value);
  switchToMockEnvironment();
  mockEnabled.value = false;
  curlCommand.value = "";
  debugResponse.value = null;
  requestFeedback.value = "已恢复示例数据，并切回内置 Mock 环境。现在可以直接点击发送。";
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
      requestFeedback.value = "请求已完成，断言通过。下面可以查看响应体和断言结果。";
      requestFeedbackType.value = "success";
    } else {
      requestFeedback.value = "请求已完成，但断言未通过。请查看下方响应与断言结果。";
      requestFeedbackType.value = "error";
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    requestFeedback.value = "请求没有成功发出。请查看页面上方错误信息。";
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

watch(selectedEndpoint, (endpoint) => syncEditor(endpoint), { immediate: true });
watch(selectedEnvironment, (environment) => syncEnvironment(environment), { immediate: true });

onMounted(async () => {
  try {
    const [endpointData, environmentData] = await Promise.all([
      getApiEndpoints(),
      getApiTestingEnvironments(),
    ]);
    endpoints.value = endpointData.items;
    environments.value = environmentData.items;
    selectedEndpointId.value = endpointData.items[0]?.endpoint_id ?? "";
    switchToMockEnvironment();
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
        <p>复现 FullScopeTest 的核心 API 工作台能力：环境变量、请求调试、Mock、断言、cURL、AI 用例裂变和编排预览。</p>
      </div>
      <button class="primary-button" :disabled="loading || !selectedEndpoint" @click="submitDebugRequest">
        {{ loading ? "处理中..." : "发送选中接口" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">接口工作台错误：{{ error }}</div>

    <div class="panel api-help-panel">
      <div class="item-title">
        <div>
          <h3>你先跑这 4 个固定用例</h3>
          <p class="muted">不用自己想数据。点一个用例后，右侧调试器会自动填好请求数据和断言。</p>
        </div>
        <button class="ghost-button" type="button" @click="resetCurrentExample">恢复当前用例默认数据</button>
      </div>
      <div class="quick-example-grid">
        <button
          v-for="example in quickExamples"
          :key="example.endpointId"
          class="quick-example-card"
          :class="{ active: example.endpointId === selectedEndpoint?.endpoint_id }"
          type="button"
          @click="selectEndpoint(example.endpointId)"
        >
          <span class="tag">{{ example.module }}</span>
          <strong>{{ example.title }}</strong>
          <small>{{ example.reason }}</small>
        </button>
      </div>
    </div>

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
        <span>环境配置</span>
        <strong>{{ environments.length }}</strong>
      </div>
      <div class="metric-card">
        <span>调试模式</span>
        <strong>{{ mockEnabled ? "Mock" : targetBaseUrl ? "HTTP" : "内置" }}</strong>
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

      <div class="panel api-request-panel">
        <div class="item-title">
          <h3>请求工作台</h3>
          <span class="tag">{{ selectedEndpoint?.related_case_id ?? "未选择" }}</span>
        </div>
        <template v-if="selectedEndpoint">
          <div class="request-name-row">
            <input class="form-control request-name-input" :value="selectedEndpoint.name" readonly />
            <button class="ghost-button" type="button" @click="resetCurrentExample">重置示例</button>
          </div>

          <div class="api-request-line request-url-row">
            <span class="method-pill">{{ selectedEndpoint.method }}</span>
            <span class="path-text">{{ selectedEndpoint.path }}</span>
            <button v-if="isLocalHttpMode" class="ghost-button" type="button" @click="switchToMockEnvironment">
              切回内置 Mock
            </button>
            <button class="primary-button" :disabled="loading" @click="submitDebugRequest">
              {{ loading ? "发送中..." : "发送" }}
            </button>
          </div>

          <div class="assistant-form-grid">
            <label>
              环境
              <select v-model="selectedEnvironmentId" class="form-control">
                <option
                  v-for="environment in environments"
                  :key="environment.environment_id"
                  :value="environment.environment_id"
                >
                  {{ environment.name }}
                </option>
              </select>
            </label>
            <label>
              Base URL
              <input v-model="targetBaseUrl" class="form-control" placeholder="留空使用内置 Mock" />
            </label>
            <label>
              Body Type
              <select v-model="bodyType" class="form-control">
                <option value="json">json</option>
                <option value="raw">raw</option>
                <option value="form">form</option>
              </select>
            </label>
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

          <div v-if="isLocalHttpMode" class="inline-warning">
            当前是本机 API 环境，会请求 {{ targetBaseUrl }}。如果你没有启动这个端口的真实接口服务，请点击
            <button class="text-button" type="button" @click="switchToMockEnvironment">切回内置 Mock</button>
            再发送。
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

          <div class="request-tab-body">
            <div v-if="activeRequestTab === 'params'" class="tab-panel">
              <label>
                Query Params JSON
                <textarea v-model="paramsEditor" class="assistant-textarea compact-textarea code-editor" rows="7" />
              </label>
              <p class="muted">大多数当前示例接口不需要 query 参数，所以保持 `{}` 即可。</p>
            </div>

            <div v-else-if="activeRequestTab === 'headers'" class="tab-panel">
              <div class="two-column compact-editor-grid">
                <label>
                  环境公共 Headers JSON
                  <textarea v-model="environmentHeadersEditor" class="assistant-textarea compact-textarea code-editor" rows="7" />
                </label>
                <label>
                  请求 Headers JSON
                  <textarea v-model="headersEditor" class="assistant-textarea compact-textarea code-editor" rows="7" />
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
                <textarea v-model="bodyEditor" class="assistant-textarea compact-textarea code-editor" rows="8" />
              </label>
            </div>

            <div v-else-if="activeRequestTab === 'assertions'" class="tab-panel assertion-editor">
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
              <textarea
                v-model="mockBody"
                class="assistant-textarea compact-textarea code-editor"
                rows="7"
              />
            </div>

            <div v-else class="tab-panel">
              <div v-if="selectedEndpointGuide" class="endpoint-guide-card">
                <div class="item-title">
                  <div>
                    <strong>当前用例在测什么</strong>
                    <p>{{ selectedEndpointGuide.goal }}</p>
                  </div>
                  <span class="status-pill ok">已填好默认数据</span>
                </div>
                <table class="data-table compact-table guide-table">
                  <tbody>
                    <tr v-for="item in selectedEndpointGuide.fields" :key="item.field">
                      <td>
                        <strong>{{ item.field }}</strong>
                      </td>
                      <td class="path-text">{{ item.fill }}</td>
                      <td>{{ item.why }}</td>
                    </tr>
                  </tbody>
                </table>
                <p class="expected-text">
                  <strong>预期结果：</strong>{{ selectedEndpointGuide.expected }}
                </p>
              </div>
            </div>
          </div>

          <div class="toolbar api-action-bar">
            <button class="primary-button" :disabled="loading" @click="submitDebugRequest">发送请求</button>
            <button class="ghost-button" :disabled="loading" @click="submitSynthesize">AI 裂变用例</button>
            <button class="ghost-button" @click="submitCurlExport">导出 cURL</button>
          </div>
        </template>
        <div v-else class="empty-state">暂无接口数据</div>
      </div>
    </div>

    <div class="two-column api-debug-section">
      <div class="panel">
        <h3>响应与断言结果</h3>
        <template v-if="debugResponse">
          <div class="toolbar">
            <span class="status-pill" :class="debugResponse.passed ? 'ok' : 'warn'">
              {{ debugResponse.passed ? "通过" : "失败" }}
            </span>
            <span class="tag">status {{ debugResponse.response.status_code }}</span>
            <span class="tag">{{ debugResponse.response.duration_ms }} ms</span>
            <span class="tag">{{ debugResponse.request.target_mode }}</span>
            <span class="tag">assert {{ debugResponse.summary.passed }}/{{ debugResponse.summary.total }}</span>
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

      <div class="panel">
        <h3>接口详情</h3>
        <template v-if="selectedEndpoint">
          <div class="item-title">
            <strong>{{ selectedEndpoint.name }}</strong>
            <span class="method-pill">{{ selectedEndpoint.method }}</span>
          </div>
          <p class="path-text">{{ selectedEndpoint.path }}</p>
          <p class="muted">{{ selectedEndpoint.description }}</p>
          <h3>关联测试用例</h3>
          <span class="tag">{{ selectedEndpoint.related_case_id }}</span>
          <h3>pytest 自动化</h3>
          <p class="path-text">{{ selectedEndpoint.pytest_target }}</p>
          <pre class="code-block">{{ selectedRunCommand }}</pre>
          <h3>cURL</h3>
          <pre v-if="curlCommand" class="mini-code">{{ curlCommand }}</pre>
          <div v-else class="empty-state">点击导出 cURL 后显示。</div>
        </template>
      </div>
    </div>

    <div class="two-column api-debug-section">
      <div class="panel">
        <div class="item-title">
          <h3>AI 数据裂变</h3>
          <span class="tag">{{ synthesizedCases.length }} cases</span>
        </div>
        <div v-if="synthesizedCases.length" class="stack">
          <article v-for="testCase in synthesizedCases" :key="testCase.name" class="endpoint-card">
            <div class="item-title">
              <strong>{{ testCase.name }}</strong>
              <span class="tag">expect {{ testCase.expected_status }}</span>
            </div>
            <p class="path-text">{{ testCase.method }} {{ testCase.path }}</p>
            <pre class="mini-code">{{ testCase.body }}</pre>
            <button class="ghost-button" type="button" @click="applySynthesizedCase(testCase)">
              应用到调试器
            </button>
          </article>
        </div>
        <div v-else class="empty-state">点击 AI 裂变用例，生成边界、异常、安全类接口用例。</div>
      </div>

      <div class="panel">
        <div class="item-title">
          <h3>AI 编排预览</h3>
          <button class="ghost-button" :disabled="loading" @click="submitPlan">生成计划</button>
        </div>
        <textarea v-model="planPrompt" class="assistant-textarea compact-textarea" rows="4" />
        <template v-if="operationPlan">
          <p class="muted">{{ operationPlan.summary }} · {{ operationPlan.source }}</p>
          <pre class="code-block">{{ JSON.stringify(operationPlan.operations, null, 2) }}</pre>
        </template>
        <div v-else class="empty-state">输入自然语言目标，生成可执行的接口测试操作计划。</div>
      </div>
    </div>
  </section>
</template>

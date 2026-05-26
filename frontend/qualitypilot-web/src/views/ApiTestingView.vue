<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { message as antMessage } from "ant-design-vue";
import {
  BulbOutlined,
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  RobotOutlined,
  SaveOutlined,
  SendOutlined,
} from "@ant-design/icons-vue";
import {
  exportApiCurl,
  getApiCollections,
  getApiEndpoints,
  getApiTestingEnvironments,
  getSavedApiCases,
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
  SavedApiCase,
} from "../types";

interface JsonAssertionEditor {
  path: string;
  operator: string;
  expected: string;
}

interface EndpointGuide {
  goal: string;
  expected: string;
  fields: Array<{
    field: string;
    fill: string;
    why: string;
  }>;
}

type RequestTab = "params" | "headers" | "body" | "pre_script" | "assertions" | "mock" | "guide";
type SidebarTab = "cases" | "collections";
type ResponseTab = "body" | "assertions" | "curl" | "plan";

const endpoints = ref<ApiEndpointItem[]>([]);
const environments = ref<ApiEnvironment[]>([]);
const collections = ref<ApiCollection[]>([]);
const savedCases = ref<SavedApiCase[]>([]);
const selectedEndpointId = ref("");
const selectedEnvironmentId = ref("mock-local");
const selectedModule = ref("all");
const searchKeyword = ref("");
const sidebarTab = ref<SidebarTab>("cases");
const activeRequestTab = ref<RequestTab>("body");
const activeResponseTab = ref<ResponseTab>("body");
const loading = ref(false);
const pageLoading = ref(false);
const error = ref("");
const debugResponse = ref<ApiDebugResponse | null>(null);
const synthesizedCases = ref<ApiSynthesizedCase[]>([]);
const operationPlan = ref<ApiOperationPlanResponse | null>(null);
const collectionRun = ref<PlatformRunRecord | null>(null);
const curlCommand = ref("");

const requestName = ref("");
const targetBaseUrl = ref("");
const headersEditor = ref("{}");
const paramsEditor = ref("{}");
const variablesEditor = ref("{}");
const environmentHeadersEditor = ref("{}");
const bodyEditor = ref("");
const bodyType = ref("json");
const expectedStatus = ref<number | null>(200);
const jsonAssertions = ref<JsonAssertionEditor[]>([]);
const preScriptEditor = ref("// 示例：这里可以准备 token、环境变量或动态参数。");
const postScriptEditor = ref("// 示例：这里可以提取字段、写入变量或做复杂断言。");
const mockEnabled = ref(false);
const mockStatusCode = ref(200);
const mockDelayMs = ref(0);
const mockBody = ref('{"message": "mock response"}');
const planPrompt = ref("帮我为登录接口创建测试集合，生成正常登录和异常登录用例，并执行集合。");

const endpointGuides: Record<string, EndpointGuide> = {
  "api-login-success": {
    goal: "验证登录主流程：账号 tester 和密码 Passw0rd! 正确时，接口应该返回 token。",
    expected: "HTTP 200，响应体包含 token，并且 user.username 等于 tester。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "不需要真实后端服务，适合本地演示。" },
      { field: "Base URL", fill: "留空", why: "留空会走平台内置的 mock 登录接口。" },
      { field: "Request Body", fill: '{"username": "tester", "password": "Passw0rd!"}', why: "正确账号密码。" },
      { field: "断言", fill: "status=200，token exists，user.username=tester", why: "验证接口业务结果。" },
    ],
  },
  "api-login-invalid-password": {
    goal: "验证登录异常流：密码错误时不能返回 token，应该拒绝登录。",
    expected: "HTTP 401，响应体 error 等于 invalid_credentials。",
    fields: [
      { field: "环境", fill: "内置 Mock 环境", why: "稳定演示异常分支。" },
      { field: "Request Body", fill: '{"username": "tester", "password": "wrong"}', why: "故意传错误密码。" },
      { field: "断言", fill: "status=401，error=invalid_credentials", why: "验证鉴权失败处理。" },
    ],
  },
  "api-upload-success": {
    goal: "验证文件上传主流程：传入文件内容和文件名，接口应该返回文件名和大小。",
    expected: "HTTP 201，响应体 filename 等于 demo.txt，并且 size 存在。",
    fields: [
      { field: "Body Type", fill: "raw", why: "这里模拟二进制文件内容，不是 JSON。" },
      { field: "Headers", fill: "Content-Type + X-Filename", why: "X-Filename 表示上传文件名。" },
      { field: "Request Body", fill: "demo-binary-content", why: "用字符串模拟文件内容。" },
      { field: "断言", fill: "status=201，filename=demo.txt，size exists", why: "验证上传结果。" },
    ],
  },
  "api-upload-missing-filename": {
    goal: "验证文件上传参数校验：缺少文件名 header 时，接口应该返回参数错误。",
    expected: "HTTP 400，响应体 error 等于 missing_filename。",
    fields: [
      { field: "Headers", fill: "只保留 Content-Type", why: "故意不传 X-Filename。" },
      { field: "Request Body", fill: "demo-binary-content", why: "文件内容存在，但文件名缺失。" },
      { field: "断言", fill: "status=400，error=missing_filename", why: "验证参数校验逻辑。" },
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

const moduleOptions = computed(() => [
  { label: "全部模块", value: "all" },
  ...Array.from(new Set(endpoints.value.map((item) => item.module))).map((module) => ({
    label: module,
    value: module,
  })),
]);

const groupedEndpoints = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  const groups = new Map<string, ApiEndpointItem[]>();
  for (const endpoint of endpoints.value) {
    const moduleMatched = selectedModule.value === "all" || endpoint.module === selectedModule.value;
    const keywordMatched =
      !keyword ||
      `${endpoint.name} ${endpoint.path} ${endpoint.module} ${endpoint.related_case_id}`
        .toLowerCase()
        .includes(keyword);
    if (!moduleMatched || !keywordMatched) continue;
    groups.set(endpoint.module, [...(groups.get(endpoint.module) ?? []), endpoint]);
  }
  return Array.from(groups.entries()).map(([module, items]) => ({ module, items }));
});

const activeCollection = computed<ApiCollection | undefined>(() => {
  if (!selectedEndpoint.value) return collections.value[0];
  const collectionId = selectedEndpoint.value.module.includes("上传") ? "upload" : "auth";
  return collections.value.find((item) => item.collection_id === collectionId) ?? collections.value[0];
});

const endpointGuide = computed(() => {
  const endpointId = selectedEndpoint.value?.endpoint_id;
  return endpointId ? endpointGuides[endpointId] : undefined;
});

const requestSummary = computed(() => {
  if (!selectedEndpoint.value) return "";
  return `${selectedEndpoint.value.method} ${selectedEndpoint.value.path}`;
});

const responsePreview = computed(() => {
  if (!debugResponse.value) return "";
  return debugResponse.value.response.json
    ? JSON.stringify(debugResponse.value.response.json, null, 2)
    : debugResponse.value.response.body;
});

const canUseMockDirectly = computed(() => !targetBaseUrl.value.trim() && !mockEnabled.value);

const runCommand = computed(() => {
  const scenarioId = selectedEndpoint.value?.scenario_id ?? "api_login";
  return `.\\.venv\\Scripts\\python.exe scripts\\run_automation_suite.py --scenario ${scenarioId}`;
});

const metrics = computed(() => [
  { label: "接口用例", value: endpoints.value.length },
  { label: "接口模块", value: moduleOptions.value.length - 1 },
  { label: "环境配置", value: environments.value.length },
  { label: "已保存草稿", value: savedCases.value.length },
]);

function selectEndpoint(endpointId: string): void {
  selectedEndpointId.value = endpointId;
  debugResponse.value = null;
  synthesizedCases.value = [];
  operationPlan.value = null;
  curlCommand.value = "";
  activeRequestTab.value = "body";
  activeResponseTab.value = "body";
  mockEnabled.value = false;
  switchToMockEnvironment();
}

function syncEditor(endpoint: ApiEndpointItem | undefined): void {
  if (!endpoint) return;
  requestName.value = endpoint.name;
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
  if (!environment) return;
  targetBaseUrl.value = environment.base_url;
  variablesEditor.value = JSON.stringify(environment.variables, null, 2);
  environmentHeadersEditor.value = JSON.stringify(environment.headers, null, 2);
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

function resetCurrentExample(): void {
  syncEditor(selectedEndpoint.value);
  switchToMockEnvironment();
  mockEnabled.value = false;
  antMessage.info("已恢复当前接口的演示数据，并切回内置 Mock 环境。");
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
  activeRequestTab.value = "assertions";
  antMessage.success(`已应用用例：${testCase.name}`);
}

async function submitDebugRequest(): Promise<void> {
  loading.value = true;
  error.value = "";
  debugResponse.value = null;
  try {
    debugResponse.value = await sendApiDebugRequest(buildRequestPayload());
    activeResponseTab.value = debugResponse.value.passed ? "body" : "assertions";
    if (debugResponse.value.passed) {
      antMessage.success("请求完成，断言通过。");
    } else {
      antMessage.warning("请求完成，但存在未通过断言。");
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    antMessage.error("请求失败，请检查页面上方错误信息。");
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
    antMessage.success(`已生成 ${data.cases.length} 条 AI 裂变用例。`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitSaveCase(): Promise<void> {
  if (!selectedEndpoint.value) return;
  error.value = "";
  try {
    const payload = buildRequestPayload();
    await saveApiCase({
      name: requestName.value || selectedEndpoint.value.name,
      method: payload.method,
      path: payload.path,
      collection_id: activeCollection.value?.collection_id ?? "auth",
      headers: payload.headers,
      body: payload.body,
      expected_status: payload.expected_status,
      json_assertions: payload.json_assertions,
    });
    await loadSavedCases();
    antMessage.success("用例草稿已保存。");
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function submitRunCollection(collectionId?: string): Promise<void> {
  const targetCollectionId = collectionId ?? activeCollection.value?.collection_id;
  if (!targetCollectionId) return;
  loading.value = true;
  error.value = "";
  try {
    collectionRun.value = await runApiCollection(targetCollectionId);
    activeResponseTab.value = "plan";
    antMessage.success(`集合执行完成：${collectionRun.value.summary.passed}/${collectionRun.value.summary.total} 通过。`);
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
    activeResponseTab.value = "curl";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
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
        active_collection_id: activeCollection.value?.collection_id,
      },
    });
    activeResponseTab.value = "plan";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function loadSavedCases(): Promise<void> {
  const data = await getSavedApiCases();
  savedCases.value = data.items;
}

async function loadPageData(): Promise<void> {
  pageLoading.value = true;
  error.value = "";
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
    selectedModule.value = endpointData.summary.modules[0] ?? "all";
    switchToMockEnvironment();
    await loadSavedCases();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    pageLoading.value = false;
  }
}

watch(selectedEndpoint, (endpoint) => syncEditor(endpoint), { immediate: true });
watch(selectedEnvironment, (environment) => syncEnvironment(environment), { immediate: true });

onMounted(loadPageData);
</script>

<template>
  <section class="qp-page api-workbench-page">
    <div class="qp-page-heading">
      <div>
        <p class="qp-eyebrow">API TESTING · RAG · MCP</p>
        <h1>API 测试工作台</h1>
        <p>参考真实测试平台的请求调试、用例管理、集合执行和 AI 用例裂变流程，默认使用内置 Mock，打开即可演示。</p>
      </div>
      <a-space>
        <a-button @click="resetCurrentExample">
          <template #icon><ReloadOutlined /></template>
          重置示例
        </a-button>
        <a-button type="primary" :loading="loading" @click="submitDebugRequest">
          <template #icon><SendOutlined /></template>
          发送请求
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="接口工作台错误"
      :description="error"
    />

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col v-for="item in metrics" :key="item.label" :xs="24" :md="6">
        <a-card class="stat-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </a-card>
      </a-col>
    </a-row>

    <a-spin :spinning="pageLoading">
      <a-layout class="api-studio">
        <a-layout-sider class="api-studio-sider" :width="312">
          <a-tabs v-model:activeKey="sidebarTab" size="small">
            <a-tab-pane key="cases" tab="测试用例">
              <a-input-search v-model:value="searchKeyword" placeholder="搜索用例、接口、模块" />
              <a-select
                v-model:value="selectedModule"
                class="full-width section-gap-sm"
                :options="moduleOptions"
              />
              <div class="api-tree">
                <section v-for="group in groupedEndpoints" :key="group.module" class="api-tree-group">
                  <strong>{{ group.module }}</strong>
                  <button
                    v-for="endpoint in group.items"
                    :key="endpoint.endpoint_id"
                    class="api-case-button"
                    :class="{ active: endpoint.endpoint_id === selectedEndpoint?.endpoint_id }"
                    type="button"
                    @click="selectEndpoint(endpoint.endpoint_id)"
                  >
                    <a-tag color="blue">{{ endpoint.method }}</a-tag>
                    <span>{{ endpoint.name }}</span>
                  </button>
                </section>
              </div>
            </a-tab-pane>
            <a-tab-pane key="collections" tab="集合管理">
              <div class="api-tree">
                <a-card v-for="collection in collections" :key="collection.collection_id" size="small">
                  <template #title>{{ collection.name }}</template>
                  <template #extra>
                    <a-tag>{{ collection.case_ids.length }} cases</a-tag>
                  </template>
                  <p>{{ collection.description }}</p>
                  <a-button block @click="submitRunCollection(collection.collection_id)">
                    <template #icon><PlayCircleOutlined /></template>
                    运行集合
                  </a-button>
                </a-card>
              </div>
            </a-tab-pane>
          </a-tabs>
        </a-layout-sider>

        <a-layout-content class="api-studio-main">
          <template v-if="selectedEndpoint">
            <a-card class="request-card" :bordered="false">
              <div class="request-topline">
                <a-input v-model:value="requestName" placeholder="请求名称" />
                <a-space>
                  <a-button @click="submitSaveCase">
                    <template #icon><SaveOutlined /></template>
                    保存
                  </a-button>
                  <a-button @click="submitSynthesize">
                    <template #icon><RobotOutlined /></template>
                    AI 扩充用例
                  </a-button>
                  <a-button @click="submitPlan">
                    <template #icon><BulbOutlined /></template>
                    AI 编排
                  </a-button>
                </a-space>
              </div>

              <div class="request-url-line">
                <a-select :value="selectedEndpoint.method" disabled>
                  <a-select-option :value="selectedEndpoint.method">{{ selectedEndpoint.method }}</a-select-option>
                </a-select>
                <a-input :value="selectedEndpoint.path" readonly />
                <a-button type="primary" size="large" :loading="loading" @click="submitDebugRequest">
                  <template #icon><SendOutlined /></template>
                  发送
                </a-button>
              </div>

              <a-row :gutter="[12, 12]" class="section-gap-sm">
                <a-col :span="8">
                  <label class="form-label">环境</label>
                  <a-select v-model:value="selectedEnvironmentId" class="full-width">
                    <a-select-option
                      v-for="environment in environments"
                      :key="environment.environment_id"
                      :value="environment.environment_id"
                    >
                      {{ environment.name }}
                    </a-select-option>
                  </a-select>
                </a-col>
                <a-col :span="10">
                  <label class="form-label">Base URL</label>
                  <a-input v-model:value="targetBaseUrl" placeholder="留空使用内置 Mock" />
                </a-col>
                <a-col :span="6">
                  <label class="form-label">Body Type</label>
                  <a-select v-model:value="bodyType" class="full-width">
                    <a-select-option value="json">json</a-select-option>
                    <a-select-option value="raw">raw</a-select-option>
                    <a-select-option value="form">form</a-select-option>
                  </a-select>
                </a-col>
              </a-row>

              <a-alert
                class="section-gap-sm"
                :type="canUseMockDirectly ? 'success' : 'warning'"
                show-icon
                :message="canUseMockDirectly ? '当前会走内置 Mock，直接点击发送即可看到响应。' : '当前配置了 Base URL 或自定义 Mock，请确认目标服务可访问。'"
              />

              <a-tabs v-model:activeKey="activeRequestTab" class="request-tabs">
                <a-tab-pane key="params" tab="Params">
                  <a-textarea v-model:value="paramsEditor" class="code-editor" :rows="8" />
                </a-tab-pane>
                <a-tab-pane key="headers" tab="Headers">
                  <a-row :gutter="12">
                    <a-col :span="12">
                      <label class="form-label">环境公共 Headers JSON</label>
                      <a-textarea v-model:value="environmentHeadersEditor" class="code-editor" :rows="8" />
                    </a-col>
                    <a-col :span="12">
                      <label class="form-label">请求 Headers JSON</label>
                      <a-textarea v-model:value="headersEditor" class="code-editor" :rows="8" />
                    </a-col>
                  </a-row>
                </a-tab-pane>
                <a-tab-pane key="body" tab="Body">
                  <a-row :gutter="12">
                    <a-col :span="9">
                      <label class="form-label">环境变量 JSON</label>
                      <a-textarea v-model:value="variablesEditor" class="code-editor" :rows="12" />
                    </a-col>
                    <a-col :span="15">
                      <label class="form-label">Request Body</label>
                      <a-textarea v-model:value="bodyEditor" class="code-editor" :rows="12" />
                    </a-col>
                  </a-row>
                </a-tab-pane>
                <a-tab-pane key="pre_script" tab="前置脚本">
                  <a-textarea v-model:value="preScriptEditor" class="code-editor" :rows="12" />
                </a-tab-pane>
                <a-tab-pane key="assertions" tab="断言脚本">
                  <a-space direction="vertical" class="full-width">
                    <a-textarea v-model:value="postScriptEditor" class="code-editor" :rows="4" />
                    <a-space>
                      <span>期望状态码</span>
                      <a-input-number v-model:value="expectedStatus" :min="0" />
                      <a-button @click="addAssertion">新增 JSON 断言</a-button>
                    </a-space>
                    <div
                      v-for="(assertion, index) in jsonAssertions"
                      :key="`${assertion.path}-${index}`"
                      class="assertion-row-v2"
                    >
                      <a-input v-model:value="assertion.path" placeholder="JSON Path，例如 token" />
                      <a-select v-model:value="assertion.operator">
                        <a-select-option value="equals">equals</a-select-option>
                        <a-select-option value="contains">contains</a-select-option>
                        <a-select-option value="exists">exists</a-select-option>
                        <a-select-option value="not_exists">not_exists</a-select-option>
                      </a-select>
                      <a-input v-model:value="assertion.expected" placeholder="期望值" />
                      <a-button danger @click="removeAssertion(index)">删除</a-button>
                    </div>
                  </a-space>
                </a-tab-pane>
                <a-tab-pane key="mock" tab="Mock">
                  <a-space direction="vertical" class="full-width">
                    <a-space>
                      <a-switch v-model:checked="mockEnabled" />
                      <span>启用自定义 Mock 响应</span>
                      <span>状态码</span>
                      <a-input-number v-model:value="mockStatusCode" :min="100" :max="599" />
                      <span>延迟 ms</span>
                      <a-input-number v-model:value="mockDelayMs" :min="0" :max="3000" />
                    </a-space>
                    <a-textarea v-model:value="mockBody" class="code-editor" :rows="9" />
                  </a-space>
                </a-tab-pane>
                <a-tab-pane key="guide" tab="说明">
                  <a-descriptions v-if="endpointGuide" bordered size="small" :column="1">
                    <a-descriptions-item label="当前用例测什么">
                      {{ endpointGuide.goal }}
                    </a-descriptions-item>
                    <a-descriptions-item label="预期结果">
                      {{ endpointGuide.expected }}
                    </a-descriptions-item>
                    <a-descriptions-item label="字段怎么填">
                      <a-table
                        size="small"
                        :pagination="false"
                        :data-source="endpointGuide.fields"
                        :columns="[
                          { title: '字段', dataIndex: 'field' },
                          { title: '填写内容', dataIndex: 'fill' },
                          { title: '为什么', dataIndex: 'why' },
                        ]"
                      />
                    </a-descriptions-item>
                  </a-descriptions>
                </a-tab-pane>
              </a-tabs>
            </a-card>

            <a-card class="section-gap" :bordered="false">
              <template #title>响应与断言结果</template>
              <template #extra>
                <a-space>
                  <a-tag v-if="debugResponse" :color="debugResponse.passed ? 'green' : 'red'">
                    {{ debugResponse.passed ? "通过" : "失败" }}
                  </a-tag>
                  <a-tag v-if="debugResponse">status {{ debugResponse.response.status_code }}</a-tag>
                  <a-tag v-if="debugResponse">{{ debugResponse.response.duration_ms }} ms</a-tag>
                  <a-button size="small" @click="submitCurlExport">
                    <template #icon><CodeOutlined /></template>
                    导出 cURL
                  </a-button>
                </a-space>
              </template>
              <a-tabs v-model:activeKey="activeResponseTab">
                <a-tab-pane key="body" tab="响应体">
                  <pre v-if="debugResponse" class="code-block">{{ responsePreview }}</pre>
                  <a-empty v-else description="点击发送请求后，这里会展示响应体。" />
                </a-tab-pane>
                <a-tab-pane key="assertions" tab="断言">
                  <a-table
                    v-if="debugResponse"
                    size="small"
                    :pagination="false"
                    :data-source="debugResponse.assertions"
                    :columns="[
                      { title: '结果', dataIndex: 'passed' },
                      { title: '断言', dataIndex: 'name' },
                      { title: '实际值', dataIndex: 'actual' },
                    ]"
                  >
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.dataIndex === 'passed'">
                        <a-tag :color="record.passed ? 'green' : 'red'">
                          {{ record.passed ? "PASS" : "FAIL" }}
                        </a-tag>
                      </template>
                    </template>
                  </a-table>
                  <a-empty v-else description="暂无断言结果。" />
                </a-tab-pane>
                <a-tab-pane key="curl" tab="cURL">
                  <pre v-if="curlCommand" class="code-block">{{ curlCommand }}</pre>
                  <a-empty v-else description="点击导出 cURL 后展示命令。" />
                </a-tab-pane>
                <a-tab-pane key="plan" tab="执行计划">
                  <pre v-if="operationPlan" class="code-block">{{ JSON.stringify(operationPlan.operations, null, 2) }}</pre>
                  <pre v-else-if="collectionRun" class="code-block">{{ JSON.stringify(collectionRun, null, 2) }}</pre>
                  <a-empty v-else description="点击 AI 编排或运行集合后展示计划。" />
                </a-tab-pane>
              </a-tabs>
            </a-card>
          </template>

          <a-empty v-else description="暂无接口数据，请确认 FastAPI 后端已启动。" />
        </a-layout-content>

        <a-layout-sider class="api-studio-right" :width="360">
          <a-card size="small" title="接口详情">
            <template v-if="selectedEndpoint">
              <p class="path-text">{{ requestSummary }}</p>
              <p>{{ selectedEndpoint.description }}</p>
              <a-space wrap>
                <a-tag>{{ selectedEndpoint.related_case_id }}</a-tag>
                <a-tag color="green">{{ selectedEndpoint.automation_status }}</a-tag>
                <a-tag color="blue">{{ selectedEndpoint.scenario_name }}</a-tag>
              </a-space>
              <pre class="mini-code">{{ runCommand }}</pre>
            </template>
          </a-card>

          <a-card size="small" title="AI 裂变用例" class="section-gap-sm">
            <template #extra>
              <a-tag>{{ synthesizedCases.length }}</a-tag>
            </template>
            <a-empty v-if="!synthesizedCases.length" description="点击 AI 扩充用例，生成边界、异常、安全用例。" />
            <a-space v-else direction="vertical" class="full-width">
              <a-card v-for="testCase in synthesizedCases" :key="testCase.name" size="small">
                <template #title>{{ testCase.name }}</template>
                <template #extra>
                  <a-tag>expect {{ testCase.expected_status }}</a-tag>
                </template>
                <pre class="mini-code">{{ testCase.body }}</pre>
                <a-button block size="small" @click="applySynthesizedCase(testCase)">应用到请求</a-button>
              </a-card>
            </a-space>
          </a-card>

          <a-card size="small" title="MCP / RAG 说明" class="section-gap-sm">
            <a-alert
              type="info"
              show-icon
              message="这个页面不是普通 Postman 克隆"
              description="接口调试只是入口。QualityPilot 会把接口用例、RAG 上下文、pytest 执行、Allure 报告和失败分析串成闭环。"
            />
            <a-space wrap class="section-gap-sm">
              <a-tag color="green">retrieve_test_context</a-tag>
              <a-tag color="blue">generate_test_cases</a-tag>
              <a-tag color="purple">run_api_tests</a-tag>
              <a-tag color="red">analyze_failure</a-tag>
            </a-space>
          </a-card>

          <a-card size="small" title="AI 编排提示词" class="section-gap-sm">
            <a-textarea v-model:value="planPrompt" :rows="4" />
            <a-button class="section-gap-sm" block @click="submitPlan">
              <template #icon><ExperimentOutlined /></template>
              生成编排计划
            </a-button>
          </a-card>
        </a-layout-sider>
      </a-layout>
    </a-spin>
  </section>
</template>

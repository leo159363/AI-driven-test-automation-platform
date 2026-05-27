import type {
  ApiEndpointResponse,
  AiModelConfigResponse,
  AiModelTestResponse,
  ApiCollectionsResponse,
  ApiDebugResponse,
  ApiEnvironment,
  ApiEnvironmentResponse,
  ApiOperationPlanResponse,
  ApiSynthesizeResponse,
  CopilotResponse,
  AutomationScenarioResponse,
  AutomationRunRecord,
  AutomationRunsResponse,
  HealthResponse,
  LatestReportResponse,
  AssistantResponse,
  KnowledgeSearchResponse,
  KnowledgeSourceTypesResponse,
  KnowledgeSourcesResponse,
  KnowledgeUploadResponse,
  GlobalSearchResponse,
  AppTestScript,
  AppTestScriptsResponse,
  CicdJobsResponse,
  PerformanceScenariosResponse,
  PlatformSetting,
  PlatformSettingsResponse,
  PlatformConfigItem,
  PlatformConfigsResponse,
  PlatformConfigType,
  PlatformDashboardResponse,
  PlatformProjectsResponse,
  PlatformRunRecord,
  PlatformWorkspaceResponse,
  SavedApiCasesResponse,
  TestingDocument,
  TestingDocumentsResponse,
  WebTestScriptsResponse,
  PromptTemplatesResponse,
  TestCaseCatalogResponse,
  TestCaseItem,
  RunReportResponse,
} from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path));
  } catch (error) {
    throw new Error(buildNetworkErrorMessage(error));
  }
  if (!response.ok) {
    throw new Error(await buildHttpErrorMessage(response));
  }
  return (await response.json()) as T;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(buildNetworkErrorMessage(error));
  }
  if (!response.ok) {
    throw new Error(await buildHttpErrorMessage(response));
  }
  return (await response.json()) as T;
}

async function putJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(buildNetworkErrorMessage(error));
  }
  if (!response.ok) {
    throw new Error(await buildHttpErrorMessage(response));
  }
  return (await response.json()) as T;
}

async function deleteJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: "DELETE",
    });
  } catch (error) {
    throw new Error(buildNetworkErrorMessage(error));
  }
  if (!response.ok) {
    throw new Error(await buildHttpErrorMessage(response));
  }
  return (await response.json()) as T;
}

async function postForm<T>(path: string, body: FormData): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: "POST",
      body,
    });
  } catch (error) {
    throw new Error(buildNetworkErrorMessage(error));
  }
  if (!response.ok) {
    throw new Error(await buildHttpErrorMessage(response));
  }
  return (await response.json()) as T;
}

function buildNetworkErrorMessage(error: unknown): string {
  const detail = error instanceof Error ? error.message : String(error);
  return `无法连接 QualityPilot FastAPI 后端：${detail}。请在项目根目录运行 .\\.venv\\Scripts\\python.exe scripts\\start_fullstack.py，并确认不要只启动 Vue。`;
}

async function buildHttpErrorMessage(response: Response): Promise<string> {
  let detail = "";
  try {
    const payload = (await response.json()) as { detail?: unknown };
    detail = payload.detail ? `，详情：${String(payload.detail)}` : "";
  } catch {
    detail = "";
  }
  return `QualityPilot API 返回错误：${response.status} ${response.statusText}${detail}`;
}

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/health");
}

export function getTestCases(): Promise<TestCaseCatalogResponse> {
  return getJson<TestCaseCatalogResponse>("/api/test-cases");
}

export function createTestCase(payload: {
  title: string;
  test_type: string;
  module: string;
  priority: string;
  method: string;
  path: string;
  collection_id: string;
  description: string;
  scenario_id: string;
  scenario_name: string;
  automation_status: string;
  pytest_target: string;
  assertion: string;
  related_report: string;
}): Promise<{ case: TestCaseItem; message: string }> {
  return postJson<{ case: TestCaseItem; message: string }>("/api/test-cases", payload);
}

export function updateTestCase(
  caseId: string,
  payload: {
    title: string;
    test_type: string;
    module: string;
    priority: string;
    method: string;
    path: string;
    collection_id: string;
    description: string;
    scenario_id: string;
    scenario_name: string;
    automation_status: string;
    pytest_target: string;
    assertion: string;
    related_report: string;
  },
): Promise<{ case: TestCaseItem; message: string }> {
  return putJson<{ case: TestCaseItem; message: string }>(
    `/api/test-cases/${encodeURIComponent(caseId)}`,
    payload,
  );
}

export function deleteTestCase(caseId: string): Promise<{ message: string }> {
  return deleteJson<{ message: string }>(`/api/test-cases/${encodeURIComponent(caseId)}`);
}

export function getApiEndpoints(): Promise<ApiEndpointResponse> {
  return getJson<ApiEndpointResponse>("/api/api-endpoints");
}

export function getApiTestingEnvironments(): Promise<ApiEnvironmentResponse> {
  return getJson<ApiEnvironmentResponse>("/api/api-testing/environments");
}

export function createApiTestingEnvironment(payload: {
  name: string;
  base_url: string;
  description: string;
  variables: Record<string, string>;
  headers: Record<string, string>;
  is_default: boolean;
}): Promise<{ environment: ApiEnvironment; message: string }> {
  return postJson<{ environment: ApiEnvironment; message: string }>(
    "/api/api-testing/environments",
    payload,
  );
}

export function updateApiTestingEnvironment(
  environmentId: string,
  payload: {
    name: string;
    base_url: string;
    description: string;
    variables: Record<string, string>;
    headers: Record<string, string>;
    is_default: boolean;
  },
): Promise<{ environment: ApiEnvironment; message: string }> {
  return putJson<{ environment: ApiEnvironment; message: string }>(
    `/api/api-testing/environments/${encodeURIComponent(environmentId)}`,
    payload,
  );
}

export function deleteApiTestingEnvironment(environmentId: string): Promise<{ message: string }> {
  return deleteJson<{ message: string }>(
    `/api/api-testing/environments/${encodeURIComponent(environmentId)}`,
  );
}

export function getApiCollections(): Promise<ApiCollectionsResponse> {
  return getJson<ApiCollectionsResponse>("/api/api-testing/collections");
}

export function getSavedApiCases(): Promise<SavedApiCasesResponse> {
  return getJson<SavedApiCasesResponse>("/api/api-testing/cases");
}

export function saveApiCase(payload: {
  name: string;
  method: string;
  path: string;
  collection_id: string;
  headers: Record<string, string>;
  body: string;
  expected_status: number | null;
  json_assertions: Array<{
    path: string;
    operator: string;
    expected: string;
  }>;
}): Promise<{ case: unknown; message: string }> {
  return postJson<{ case: unknown; message: string }>("/api/api-testing/cases", payload);
}

export function runApiCollection(collectionId: string): Promise<PlatformRunRecord> {
  return postJson<PlatformRunRecord>(`/api/api-testing/collections/${collectionId}/run`, {});
}

export function sendApiDebugRequest(payload: {
  method: string;
  path: string;
  base_url: string;
  headers: Record<string, string>;
  params: Record<string, string>;
  body: string;
  body_type: string;
  environment: Partial<ApiEnvironment>;
  mock_config: Record<string, unknown>;
  expected_status: number | null;
  json_assertions: Array<{
    path: string;
    operator: string;
    expected: string;
  }>;
  timeout_seconds: number;
}): Promise<ApiDebugResponse> {
  return postJson<ApiDebugResponse>("/api/api-testing/debug", payload);
}

export function synthesizeApiCases(payload: {
  method: string;
  path: string;
  headers: Record<string, string>;
  body: string;
  count: number;
}): Promise<ApiSynthesizeResponse> {
  return postJson<ApiSynthesizeResponse>("/api/api-testing/synthesize", payload);
}

export function planApiOperations(payload: {
  prompt: string;
  context: Record<string, unknown>;
}): Promise<ApiOperationPlanResponse> {
  return postJson<ApiOperationPlanResponse>("/api/api-testing/plan", payload);
}

export function exportApiCurl(payload: {
  method: string;
  path: string;
  base_url: string;
  headers: Record<string, string>;
  params: Record<string, string>;
  body: string;
  body_type: string;
  environment: Partial<ApiEnvironment>;
  mock_config: Record<string, unknown>;
  expected_status: number | null;
  json_assertions: Array<{
    path: string;
    operator: string;
    expected: string;
  }>;
  timeout_seconds: number;
}): Promise<{ curl: string }> {
  return postJson<{ curl: string }>("/api/api-testing/curl", payload);
}

export function getAutomationScenarios(): Promise<AutomationScenarioResponse> {
  return getJson<AutomationScenarioResponse>("/api/automation/scenarios");
}

export function runAutomationScenario(
  scenarioId: string,
  timeoutSeconds = 120,
): Promise<AutomationRunRecord> {
  return postJson<AutomationRunRecord>("/api/automation/run", {
    scenario_id: scenarioId,
    timeout_seconds: timeoutSeconds,
  });
}

export function getAutomationRuns(): Promise<AutomationRunsResponse> {
  return getJson<AutomationRunsResponse>("/api/automation/runs");
}

export function getLatestReport(): Promise<LatestReportResponse> {
  return getJson<LatestReportResponse>("/api/reports/latest");
}

export function getRunReport(runId: string): Promise<RunReportResponse> {
  return getJson<RunReportResponse>(`/api/reports/${encodeURIComponent(runId)}`);
}

export function getPromptTemplates(): Promise<PromptTemplatesResponse> {
  return getJson<PromptTemplatesResponse>("/api/assistant/templates");
}

export function sendAssistantMessage(payload: {
  template_id: string;
  message: string;
  project: string;
  module: string;
  version: string;
  use_knowledge: boolean;
  source_types: string[];
  top_k: number;
}): Promise<AssistantResponse> {
  return postJson<AssistantResponse>("/api/assistant/chat", payload);
}

export function getKnowledgeSourceTypes(): Promise<KnowledgeSourceTypesResponse> {
  return getJson<KnowledgeSourceTypesResponse>("/api/knowledge/source-types");
}

export function getKnowledgeSources(params: {
  project?: string;
  module?: string;
  version?: string;
  source_types?: string[];
} = {}): Promise<KnowledgeSourcesResponse> {
  const query = new URLSearchParams();
  if (params.project) query.set("project", params.project);
  if (params.module) query.set("module", params.module);
  if (params.version) query.set("version", params.version);
  for (const sourceType of params.source_types ?? []) {
    query.append("source_types", sourceType);
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return getJson<KnowledgeSourcesResponse>(`/api/knowledge/sources${suffix}`);
}

export function searchKnowledge(payload: {
  query: string;
  project: string;
  module: string;
  version: string;
  source_types: string[];
  top_k: number;
}): Promise<KnowledgeSearchResponse> {
  return postJson<KnowledgeSearchResponse>("/api/knowledge/search", payload);
}

export function uploadKnowledgeDocument(payload: {
  file: File;
  project: string;
  module: string;
  version: string;
  source_type: string;
  title: string;
}): Promise<KnowledgeUploadResponse> {
  const body = new FormData();
  body.append("file", payload.file);
  body.append("project", payload.project);
  body.append("module", payload.module);
  body.append("version", payload.version);
  body.append("source_type", payload.source_type);
  body.append("title", payload.title);
  return postForm<KnowledgeUploadResponse>("/api/knowledge/upload", body);
}

export function getPlatformWorkspace(): Promise<PlatformWorkspaceResponse> {
  return getJson<PlatformWorkspaceResponse>("/api/platform/workspace");
}

export function getPlatformProjects(): Promise<PlatformProjectsResponse> {
  return getJson<PlatformProjectsResponse>("/api/platform/projects");
}

export function getPlatformDashboard(): Promise<PlatformDashboardResponse> {
  return getJson<PlatformDashboardResponse>("/api/platform/dashboard");
}

export function getWebTestScripts(): Promise<WebTestScriptsResponse> {
  return getJson<WebTestScriptsResponse>("/api/platform/web-tests/scripts");
}

export function getAppTestScripts(): Promise<AppTestScriptsResponse> {
  return getJson<AppTestScriptsResponse>("/api/platform/app-tests/scripts");
}

export function createAppTestScript(payload: {
  name: string;
  description: string;
  platform: string;
  automation_engine: string;
  case_set: string;
  priority: string;
  device: string;
  status: string;
  pytest_target: string;
  steps: string[];
  assertions: string[];
}): Promise<{ script: AppTestScript; message: string }> {
  return postJson<{ script: AppTestScript; message: string }>(
    "/api/platform/app-tests/scripts",
    payload,
  );
}

export function updateAppTestScript(
  scriptId: string,
  payload: {
    name: string;
    description: string;
    platform: string;
    automation_engine: string;
    case_set: string;
    priority: string;
    device: string;
    status: string;
    pytest_target: string;
    steps: string[];
    assertions: string[];
  },
): Promise<{ script: AppTestScript; message: string }> {
  return putJson<{ script: AppTestScript; message: string }>(
    `/api/platform/app-tests/scripts/${encodeURIComponent(scriptId)}`,
    payload,
  );
}

export function deleteAppTestScript(scriptId: string): Promise<{ message: string }> {
  return deleteJson<{ message: string }>(
    `/api/platform/app-tests/scripts/${encodeURIComponent(scriptId)}`,
  );
}

export function getPerformanceScenarios(): Promise<PerformanceScenariosResponse> {
  return getJson<PerformanceScenariosResponse>("/api/platform/performance/scenarios");
}

export function getCicdJobs(): Promise<CicdJobsResponse> {
  return getJson<CicdJobsResponse>("/api/platform/cicd/jobs");
}

export function getTestingDocuments(): Promise<TestingDocumentsResponse> {
  return getJson<TestingDocumentsResponse>("/api/platform/documents");
}

export function createTestingDocument(payload: {
  title: string;
  category: string;
  template: string;
  path: string;
  purpose: string;
  rag_ready: boolean;
}): Promise<{ document: TestingDocument; message: string }> {
  return postJson<{ document: TestingDocument; message: string }>("/api/platform/documents", payload);
}

export function updateTestingDocument(
  docId: string,
  payload: {
    title: string;
    category: string;
    template: string;
    path: string;
    purpose: string;
    rag_ready: boolean;
  },
): Promise<{ document: TestingDocument; message: string }> {
  return putJson<{ document: TestingDocument; message: string }>(
    `/api/platform/documents/${encodeURIComponent(docId)}`,
    payload,
  );
}

export function deleteTestingDocument(docId: string): Promise<{ message: string }> {
  return deleteJson<{ message: string }>(`/api/platform/documents/${encodeURIComponent(docId)}`);
}

export function syncTestingDocuments(): Promise<{
  message: string;
  summary: { total: number; synced: number; skipped: number };
  source_ids: string[];
}> {
  return postJson<{
    message: string;
    summary: { total: number; synced: number; skipped: number };
    source_ids: string[];
  }>("/api/platform/documents/sync", {});
}

export function getPlatformSettings(): Promise<PlatformSettingsResponse> {
  return getJson<PlatformSettingsResponse>("/api/platform/settings");
}

export function getAiModelConfig(): Promise<AiModelConfigResponse> {
  return getJson<AiModelConfigResponse>("/api/platform/settings/ai-model");
}

export function updateAiModelConfig(payload: {
  enabled: boolean;
  base_url: string;
  model: string;
  api_key: string;
  vision_base_url: string;
  vision_model: string;
  vision_api_key: string;
}): Promise<AiModelConfigResponse> {
  return putJson<AiModelConfigResponse>("/api/platform/settings/ai-model", payload);
}

export function testAiModelConfig(): Promise<AiModelTestResponse> {
  return postJson<AiModelTestResponse>("/api/platform/settings/ai-model/test", {});
}

export function createPlatformSetting(payload: {
  name: string;
  value: string;
  description: string;
}): Promise<{ setting: PlatformSetting; message: string }> {
  return postJson<{ setting: PlatformSetting; message: string }>("/api/platform/settings", payload);
}

export function updatePlatformSetting(
  settingId: string,
  payload: {
    name: string;
    value: string;
    description: string;
  },
): Promise<{ setting: PlatformSetting; message: string }> {
  return putJson<{ setting: PlatformSetting; message: string }>(
    `/api/platform/settings/${encodeURIComponent(settingId)}`,
    payload,
  );
}

export function deletePlatformSetting(settingId: string): Promise<{ message: string }> {
  return deleteJson<{ message: string }>(
    `/api/platform/settings/${encodeURIComponent(settingId)}`,
  );
}

export function getPlatformConfigs(): Promise<PlatformConfigsResponse> {
  return getJson<PlatformConfigsResponse>("/api/settings/platform-configs");
}

export function createPlatformConfig(payload: {
  key: string;
  name: string;
  type: PlatformConfigType;
  enabled: boolean;
  value: Record<string, unknown>;
  description: string;
}): Promise<{ config: PlatformConfigItem }> {
  return postJson<{ config: PlatformConfigItem }>("/api/settings/platform-configs", payload);
}

export function updatePlatformConfig(
  configKey: string,
  payload: {
    name?: string;
    type?: PlatformConfigType;
    enabled?: boolean;
    value?: Record<string, unknown>;
    description?: string;
  },
): Promise<{ config: PlatformConfigItem }> {
  return putJson<{ config: PlatformConfigItem }>(
    `/api/settings/platform-configs/${encodeURIComponent(configKey)}`,
    payload,
  );
}

export function deletePlatformConfig(configKey: string): Promise<{ message: string }> {
  return deleteJson<{ message: string }>(
    `/api/settings/platform-configs/${encodeURIComponent(configKey)}`,
  );
}

export function runWebTestScript(scriptId: string): Promise<PlatformRunRecord> {
  return postJson<PlatformRunRecord>(`/api/platform/web-tests/scripts/${scriptId}/run`, {});
}

export function runAppTestScript(scriptId: string): Promise<PlatformRunRecord> {
  return postJson<PlatformRunRecord>(`/api/platform/app-tests/scripts/${scriptId}/run`, {});
}

export function runPerformanceScenario(scenarioId: string): Promise<PlatformRunRecord> {
  return postJson<PlatformRunRecord>(`/api/platform/performance/scenarios/${scenarioId}/run`, {});
}

export function runCicdJob(jobId: string): Promise<PlatformRunRecord> {
  return postJson<PlatformRunRecord>(`/api/platform/cicd/jobs/${jobId}/run`, {});
}

export function globalSearch(keyword: string): Promise<GlobalSearchResponse> {
  return postJson<GlobalSearchResponse>("/api/platform/global-search", { keyword });
}

export function sendCopilotMessage(message: string): Promise<CopilotResponse> {
  return postJson<CopilotResponse>("/api/platform/copilot/chat", { message });
}

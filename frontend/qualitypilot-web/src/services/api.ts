import type {
  ApiEndpointResponse,
  ApiDebugResponse,
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
  PromptTemplatesResponse,
  TestCaseCatalogResponse,
  RunReportResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

async function postForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/health");
}

export function getTestCases(): Promise<TestCaseCatalogResponse> {
  return getJson<TestCaseCatalogResponse>("/api/test-cases");
}

export function getApiEndpoints(): Promise<ApiEndpointResponse> {
  return getJson<ApiEndpointResponse>("/api/api-endpoints");
}

export function sendApiDebugRequest(payload: {
  method: string;
  path: string;
  base_url: string;
  headers: Record<string, string>;
  body: string;
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

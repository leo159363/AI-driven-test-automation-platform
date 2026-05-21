import type {
  ApiEndpointResponse,
  AutomationScenarioResponse,
  AutomationRunRecord,
  AutomationRunsResponse,
  HealthResponse,
  LatestReportResponse,
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

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/health");
}

export function getTestCases(): Promise<TestCaseCatalogResponse> {
  return getJson<TestCaseCatalogResponse>("/api/test-cases");
}

export function getApiEndpoints(): Promise<ApiEndpointResponse> {
  return getJson<ApiEndpointResponse>("/api/api-endpoints");
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

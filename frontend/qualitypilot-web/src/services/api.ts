import type {
  ApiEndpointResponse,
  AutomationScenarioResponse,
  HealthResponse,
  LatestReportResponse,
  TestCaseCatalogResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
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

export function getLatestReport(): Promise<LatestReportResponse> {
  return getJson<LatestReportResponse>("/api/reports/latest");
}


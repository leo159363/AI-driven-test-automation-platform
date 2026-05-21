export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  docs: string;
}

export interface TestCaseItem {
  case_id: string;
  title: string;
  test_type: string;
  module: string;
  priority: string;
  scenario_id: string;
  scenario_name: string;
  automation_status: string;
  pytest_target: string;
  assertion: string;
  related_report: string;
}

export interface TestCaseSummary {
  total: number;
  api: number;
  ui: number;
  automated: number;
}

export interface TestCaseCatalogResponse {
  items: TestCaseItem[];
  summary: TestCaseSummary;
}

export interface ApiEndpointItem {
  name: string;
  method: string;
  path: string;
  request_example: string;
  expected_result: string;
  related_case_id: string;
}

export interface ApiEndpointResponse {
  items: ApiEndpointItem[];
  summary: {
    total: number;
    methods: Record<string, number>;
    modules: string[];
  };
}

export interface AutomationScenario {
  scenario_id: string;
  name: string;
  category: string;
  description: string;
  pytest_targets: string[];
  labels: string[];
  runner_command: string;
}

export interface AutomationScenarioResponse {
  items: AutomationScenario[];
  summary: {
    total: number;
    categories: string[];
  };
}

export interface ReportArtifact {
  artifact_type: string;
  label: string;
  path: string;
  relative_path: string;
  exists: boolean;
  detail: string;
}

export interface ExecutionSummary {
  source_path: string;
  suite_name: string;
  total: number;
  passed: number;
  failed: number;
  errors: number;
  skipped: number;
  duration_seconds: number;
}

export interface LatestReportResponse {
  junit_path: string;
  summary: ExecutionSummary | null;
  warning: string | null;
  artifacts: ReportArtifact[];
}


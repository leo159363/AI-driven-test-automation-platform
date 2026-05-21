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
  endpoint_id: string;
  name: string;
  module: string;
  method: string;
  path: string;
  description: string;
  headers: Record<string, string>;
  request_example: string;
  request_body: string;
  assertions: string[];
  expected_result: string;
  related_case_id: string;
  scenario_id: string;
  scenario_name: string;
  pytest_target: string;
  automation_status: string;
  last_run_status: string;
}

export interface ApiEndpointResponse {
  items: ApiEndpointItem[];
  summary: {
    total: number;
    methods: Record<string, number>;
    modules: string[];
    scenarios: string[];
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

export interface AutomationRunSummary {
  total: number;
  passed: number;
  failed: number;
  errors: number;
  skipped: number;
  duration_seconds: number;
}

export interface AutomationRunPaths {
  run_dir: string;
  junitxml: string;
  allure_results: string;
  run_record: string;
}

export interface AutomationRunRecord {
  run_id: string;
  scenario_id: string;
  scenario_name: string;
  category: string;
  status: string;
  return_code: number;
  timed_out: boolean;
  started_at: string;
  finished_at: string;
  duration_seconds: number;
  command: string[];
  summary: AutomationRunSummary | null;
  paths: AutomationRunPaths;
  stdout: string;
  stderr: string;
}

export interface AutomationRunsResponse {
  items: AutomationRunRecord[];
  summary: {
    total: number;
    passed: number;
    failed: number;
    timeout: number;
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

export interface RunReportResponse {
  run_id: string;
  scenario_id: string;
  scenario_name: string;
  status: string;
  summary: AutomationRunSummary | null;
  paths: AutomationRunPaths;
  stdout: string;
  stderr: string;
}

export interface PromptTemplate {
  template_id: string;
  name: string;
  category: string;
  description: string;
  recommended_tools: string[];
  default_source_types: string[];
  placeholder: string;
}

export interface PromptTemplatesResponse {
  items: PromptTemplate[];
  summary: {
    total: number;
    categories: string[];
  };
}

export interface AssistantContext {
  chunk_id: string;
  source_id: string;
  source_type: string;
  title: string;
  content: string;
  score: number;
  metadata: Record<string, string>;
}

export interface AssistantResponse {
  template: PromptTemplate;
  message: string;
  project: string;
  module: string;
  version: string;
  use_knowledge: boolean;
  contexts: AssistantContext[];
  result_type: string;
  result: Record<string, unknown>;
  markdown: string;
  recommended_next_steps: string[];
}

export interface KnowledgeSource {
  source_id: string;
  title: string;
  source_type: string;
  project: string;
  module: string;
  version: string;
  chunk_count: number;
  origin: string;
  created_at: string;
}

export interface KnowledgeSourceTypesResponse {
  items: string[];
  summary: {
    total: number;
  };
}

export interface KnowledgeSourcesResponse {
  items: KnowledgeSource[];
  summary: {
    total: number;
    source_types: string[];
    modules: string[];
  };
}

export type KnowledgeContext = AssistantContext;

export interface KnowledgeSearchResponse {
  query: string;
  contexts: KnowledgeContext[];
  retrieval_mode: string;
  filters: {
    project: string;
    module: string;
    version: string;
    source_types: string[];
    top_k: number;
  };
}

export interface KnowledgeUploadResponse {
  source: KnowledgeSource;
  message: string;
}

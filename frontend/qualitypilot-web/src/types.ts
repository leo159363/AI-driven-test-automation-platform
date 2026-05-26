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

export interface ApiDebugAssertion {
  type: string;
  name: string;
  path?: string;
  operator?: string;
  passed: boolean;
  actual: unknown;
  expected: unknown;
}

export interface ApiEnvironment {
  environment_id: string;
  name: string;
  description: string;
  base_url: string;
  variables: Record<string, string>;
  headers: Record<string, string>;
}

export interface ApiEnvironmentResponse {
  items: ApiEnvironment[];
  summary: {
    total: number;
  };
}

export interface ApiDebugResponse {
  request: {
    method: string;
    path: string;
    base_url: string;
    headers: Record<string, string>;
    params: Record<string, string>;
    body: string;
    body_type: string;
    environment: ApiEnvironment;
    target_mode: string;
  };
  response: {
    status_code: number;
    headers: Record<string, string>;
    body: string;
    json: unknown;
    duration_ms: number;
  };
  assertions: ApiDebugAssertion[];
  passed: boolean;
  summary: {
    total: number;
    passed: number;
    failed: number;
  };
}

export interface ApiSynthesizedCase {
  name: string;
  method: string;
  path: string;
  headers: Record<string, string>;
  body: string;
  expected_status: number;
  json_assertions: Array<{
    path: string;
    operator: string;
    expected?: string;
  }>;
}

export interface ApiSynthesizeResponse {
  source: string;
  base_request: {
    method: string;
    path: string;
    headers: Record<string, string>;
    body: string;
  };
  cases: ApiSynthesizedCase[];
  summary: {
    total: number;
    dimensions: string[];
  };
}

export interface ApiOperationPlanResponse {
  summary: string;
  source: string;
  context: Record<string, unknown>;
  operations: Array<Record<string, unknown>>;
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

export interface PlatformProject {
  project_id: string;
  name: string;
  description: string;
  modules: string[];
  stack: string[];
}

export interface WebTestScript {
  script_id: string;
  name: string;
  module: string;
  framework: string;
  status: string;
  priority: string;
  target_url: string;
  steps: string[];
  assertions: string[];
  pytest_target: string;
  ai_capability: string;
  rag_sources: string[];
}

export interface AppTestScript {
  script_id: string;
  name: string;
  module: string;
  platform: string;
  status: string;
  priority: string;
  scope: string;
  steps: string[];
  assertions: string[];
  ai_capability: string;
}

export interface PerformanceScenario {
  scenario_id: string;
  name: string;
  module: string;
  tool: string;
  status: string;
  users: number;
  spawn_rate: number;
  duration: string;
  target: string;
  metrics: Record<string, string | number>;
  risk: string;
  command: string;
}

export interface CicdJob {
  job_id: string;
  name: string;
  trigger: string;
  status: string;
  stages: string[];
  command: string;
  quality_gate: string;
}

export interface TestingDocument {
  doc_id: string;
  title: string;
  category: string;
  path: string;
  purpose: string;
  rag_ready: boolean;
}

export interface PlatformSetting {
  setting_id: string;
  name: string;
  value: string;
  description: string;
}

export interface PlatformWorkspaceResponse {
  project: PlatformProject;
  web_tests: WebTestScript[];
  app_tests: AppTestScript[];
  performance: PerformanceScenario[];
  cicd: CicdJob[];
  documents: TestingDocument[];
  settings: PlatformSetting[];
  differentiation: string[];
}

export interface WebTestScriptsResponse {
  items: WebTestScript[];
  summary: {
    total: number;
    frameworks: string[];
    modules: string[];
  };
}

export interface AppTestScriptsResponse {
  items: AppTestScript[];
  summary: {
    total: number;
  };
}

export interface PerformanceScenariosResponse {
  items: PerformanceScenario[];
  summary: {
    total: number;
    tools: string[];
    ready: number;
  };
}

export interface CicdJobsResponse {
  items: CicdJob[];
  summary: {
    total: number;
    ready: number;
  };
}

export interface TestingDocumentsResponse {
  items: TestingDocument[];
  summary: {
    total: number;
    rag_ready: number;
    categories: string[];
  };
}

export interface PlatformSettingsResponse {
  items: PlatformSetting[];
  summary: {
    total: number;
  };
}

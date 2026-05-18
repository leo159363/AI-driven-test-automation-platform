"""Dashboard services package."""

from src.observability.dashboard.services.automation_scenario_service import (
    AutomationScenario,
    build_runner_command,
    get_automation_scenario,
    get_pytest_targets,
    list_automation_scenarios,
)
from src.observability.dashboard.services.api_execution_adapter import (
    ApiExecutionAdapter,
    ExecutionResult,
    ExecutionStepResult,
    execute_plan_with_api_adapter,
)
from src.observability.dashboard.services.execution_plan_service import (
    ExecutionPlan,
    ExecutionStep,
    build_execution_plan,
    get_execution_preset_steps,
)
from src.observability.dashboard.services.test_design_service import (
    KnowledgeHit,
    SOURCE_TYPE_LABELS,
    TestDesignDraft,
    build_test_outline,
    format_knowledge_hit_title,
    generate_test_design_draft,
    get_default_query,
    get_focus_areas,
    get_scenario_blueprint,
    infer_source_type,
    normalize_source_type,
    retrieve_knowledge_hits,
)
from src.observability.dashboard.services.test_report_service import (
    ReportArtifact,
    TestExecutionSummary,
    discover_report_artifacts,
    get_default_junit_report_path,
    load_execution_summary,
    parse_junit_xml,
)
from src.observability.dashboard.services.test_design_templates import (
    FOCUS_OPTIONS,
    SCENARIO_BLUEPRINTS,
)

__all__ = [
    "AutomationScenario",
    "ApiExecutionAdapter",
    "ExecutionPlan",
    "ExecutionResult",
    "ExecutionStep",
    "ExecutionStepResult",
    "FOCUS_OPTIONS",
    "KnowledgeHit",
    "build_execution_plan",
    "build_runner_command",
    "execute_plan_with_api_adapter",
    "get_automation_scenario",
    "get_execution_preset_steps",
    "get_pytest_targets",
    "list_automation_scenarios",
    "SCENARIO_BLUEPRINTS",
    "TestDesignDraft",
    "ReportArtifact",
    "SOURCE_TYPE_LABELS",
    "TestExecutionSummary",
    "build_test_outline",
    "discover_report_artifacts",
    "format_knowledge_hit_title",
    "generate_test_design_draft",
    "get_default_junit_report_path",
    "get_default_query",
    "get_focus_areas",
    "get_scenario_blueprint",
    "infer_source_type",
    "load_execution_summary",
    "normalize_source_type",
    "parse_junit_xml",
    "retrieve_knowledge_hits",
]

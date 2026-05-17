"""Dashboard services package."""

from src.observability.dashboard.services.automation_scenario_service import (
    AutomationScenario,
    build_runner_command,
    get_automation_scenario,
    get_pytest_targets,
    list_automation_scenarios,
)
from src.observability.dashboard.services.test_design_service import (
    KnowledgeHit,
    TestDesignDraft,
    build_test_outline,
    generate_test_design_draft,
    get_default_query,
    get_focus_areas,
    get_scenario_blueprint,
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
    "FOCUS_OPTIONS",
    "KnowledgeHit",
    "build_runner_command",
    "get_automation_scenario",
    "get_pytest_targets",
    "list_automation_scenarios",
    "SCENARIO_BLUEPRINTS",
    "TestDesignDraft",
    "ReportArtifact",
    "TestExecutionSummary",
    "build_test_outline",
    "discover_report_artifacts",
    "generate_test_design_draft",
    "get_default_junit_report_path",
    "get_default_query",
    "get_focus_areas",
    "get_scenario_blueprint",
    "load_execution_summary",
    "parse_junit_xml",
    "retrieve_knowledge_hits",
]

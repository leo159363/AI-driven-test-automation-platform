"""Dashboard services package."""

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
    "FOCUS_OPTIONS",
    "KnowledgeHit",
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

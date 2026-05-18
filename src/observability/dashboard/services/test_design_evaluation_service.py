"""Deterministic evaluation for generated test-design drafts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from src.observability.dashboard.services.test_design_service import (
    KnowledgeHit,
    generate_test_design_draft,
    infer_source_type,
    normalize_source_type,
)


DEFAULT_TEST_DESIGN_GOLDEN_SET = Path("tests/fixtures/test_design_golden_set.json")
DEFAULT_TEST_DESIGN_REPORT_DIR = Path("data/evaluation")


@dataclass(frozen=True)
class TestDesignEvaluationCase:
    """One deterministic requirement-to-test-design evaluation case."""

    case_id: str
    scenario: str
    requirement: str
    focus_areas: List[str]
    expected_keywords: List[str]
    expected_focus_areas: List[str]
    evidence: List[KnowledgeHit] = field(default_factory=list)
    expected_citation_sources: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TestDesignCaseResult:
    """Evaluation result for one golden test-design case."""

    case_id: str
    scenario: str
    metrics: Dict[str, float]
    missing_keywords: List[str]
    missing_focus_areas: List[str]
    missing_citation_sources: List[str]
    generated_markdown: str

    def to_row(self) -> Dict[str, str]:
        """Return a table-friendly row for dashboards or CLI output."""
        return {
            "Case": self.case_id,
            "Scenario": self.scenario,
            "Requirement": f"{self.metrics['requirement_coverage']:.3f}",
            "Dimension": f"{self.metrics['dimension_coverage']:.3f}",
            "Citation": f"{self.metrics['citation_coverage']:.3f}",
            "Non-empty": f"{self.metrics['non_empty_output']:.3f}",
            "Overall": f"{self.metrics['overall_score']:.3f}",
        }


@dataclass(frozen=True)
class TestDesignEvaluationReport:
    """Aggregated report for test-design generation quality."""

    test_set_path: str
    version: str
    case_results: List[TestDesignCaseResult]
    aggregate_metrics: Dict[str, float]
    total_elapsed_ms: float

    @property
    def case_count(self) -> int:
        """Return the number of evaluated cases."""
        return len(self.case_results)

    def to_rows(self) -> List[Dict[str, str]]:
        """Return rows for dashboard or CLI table rendering."""
        return [result.to_row() for result in self.case_results]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the report to JSON-compatible data."""
        return {
            "test_set_path": self.test_set_path,
            "version": self.version,
            "case_count": self.case_count,
            "aggregate_metrics": {
                key: round(value, 4) for key, value in self.aggregate_metrics.items()
            },
            "total_elapsed_ms": round(self.total_elapsed_ms, 2),
            "case_results": [asdict(result) for result in self.case_results],
        }


def load_test_design_golden_set(
    path: str | Path = DEFAULT_TEST_DESIGN_GOLDEN_SET,
) -> List[TestDesignEvaluationCase]:
    """Load and validate the test-design Golden Test Set."""
    test_set_path = Path(path)
    with test_set_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    raw_cases = payload.get("test_cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Invalid test-design golden set: missing non-empty 'test_cases'.")

    cases: List[TestDesignEvaluationCase] = []
    for index, item in enumerate(raw_cases, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"Invalid test case at index {index}: expected object.")

        case_id = _required_str(item, "id", index)
        scenario = _required_str(item, "scenario", index)
        requirement = _required_str(item, "requirement", index)
        focus_areas = _required_str_list(item, "focus_areas", index)
        expected_keywords = _required_str_list(item, "expected_keywords", index)
        expected_focus_areas = _optional_str_list(
            item,
            "expected_focus_areas",
            default=focus_areas,
        )
        expected_citation_sources = _optional_str_list(
            item,
            "expected_citation_sources",
            default=[],
        )

        evidence = [
            _knowledge_hit_from_mapping(raw_hit)
            for raw_hit in item.get("evidence", [])
            if isinstance(raw_hit, Mapping)
        ]
        cases.append(
            TestDesignEvaluationCase(
                case_id=case_id,
                scenario=scenario,
                requirement=requirement,
                focus_areas=focus_areas,
                expected_keywords=expected_keywords,
                expected_focus_areas=expected_focus_areas,
                evidence=evidence,
                expected_citation_sources=expected_citation_sources,
            )
        )
    return cases


def run_test_design_evaluation(
    test_set_path: str | Path = DEFAULT_TEST_DESIGN_GOLDEN_SET,
) -> TestDesignEvaluationReport:
    """Run deterministic test-design evaluation against a Golden Test Set."""
    started_at = time.perf_counter()
    path = Path(test_set_path)
    cases = load_test_design_golden_set(path)

    case_results = [evaluate_test_design_case(case) for case in cases]
    aggregate_metrics = _aggregate_metrics(case_results)
    total_elapsed_ms = (time.perf_counter() - started_at) * 1000

    version = _load_version(path)
    return TestDesignEvaluationReport(
        test_set_path=str(path),
        version=version,
        case_results=case_results,
        aggregate_metrics=aggregate_metrics,
        total_elapsed_ms=total_elapsed_ms,
    )


def evaluate_test_design_case(case: TestDesignEvaluationCase) -> TestDesignCaseResult:
    """Evaluate one golden case using the current deterministic draft builder."""
    draft = generate_test_design_draft(
        scenario=case.scenario,
        requirement=case.requirement,
        focus_areas=case.focus_areas,
        evidence=case.evidence,
    )
    markdown = draft.markdown

    requirement_score, missing_keywords = _text_coverage(
        markdown,
        case.expected_keywords,
    )
    dimension_score, missing_focus_areas = _focus_area_coverage(
        markdown,
        draft.focus_areas,
        case.expected_focus_areas,
    )
    citation_score, missing_citations = _citation_coverage(
        markdown,
        case.expected_citation_sources,
    )
    non_empty_output = 1.0 if markdown.strip() else 0.0

    metrics = {
        "requirement_coverage": requirement_score,
        "dimension_coverage": dimension_score,
        "citation_coverage": citation_score,
        "non_empty_output": non_empty_output,
    }
    metrics["overall_score"] = _average(metrics.values())

    return TestDesignCaseResult(
        case_id=case.case_id,
        scenario=case.scenario,
        metrics=metrics,
        missing_keywords=missing_keywords,
        missing_focus_areas=missing_focus_areas,
        missing_citation_sources=missing_citations,
        generated_markdown=markdown,
    )


def write_test_design_evaluation_report(
    report: TestDesignEvaluationReport,
    output_path: str | Path,
    project_root: str | Path = ".",
) -> Path:
    """Write an evaluation report under data/evaluation after explicit request."""
    root = Path(project_root).resolve()
    output = Path(output_path)
    if not output.is_absolute():
        output = root / output

    allowed_dir = (root / DEFAULT_TEST_DESIGN_REPORT_DIR).resolve()
    resolved_output = output.resolve()
    if not _is_relative_to(resolved_output, allowed_dir):
        raise ValueError("Test-design evaluation reports must be written under data/evaluation/.")

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return resolved_output


def _knowledge_hit_from_mapping(raw_hit: Mapping[str, Any]) -> KnowledgeHit:
    source_path = str(raw_hit.get("source_path", "unknown"))
    source_type = normalize_source_type(raw_hit.get("source_type"))
    if source_type == "unknown":
        source_type = infer_source_type(raw_hit, source_path)
    return KnowledgeHit(
        chunk_id=str(raw_hit.get("chunk_id", source_path)),
        source_path=source_path,
        score=float(raw_hit.get("score", 1.0)),
        snippet=str(raw_hit.get("snippet", "")),
        source_type=source_type,
    )


def _required_str(item: Mapping[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid test case at index {index}: missing '{key}'.")
    return value.strip()


def _required_str_list(item: Mapping[str, Any], key: str, index: int) -> List[str]:
    values = item.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"Invalid test case at index {index}: missing non-empty '{key}'.")
    result = [str(value).strip() for value in values if str(value).strip()]
    if not result:
        raise ValueError(f"Invalid test case at index {index}: '{key}' has no usable values.")
    return result


def _optional_str_list(
    item: Mapping[str, Any],
    key: str,
    default: Sequence[str],
) -> List[str]:
    values = item.get(key, list(default))
    if not isinstance(values, list):
        return list(default)
    return [str(value).strip() for value in values if str(value).strip()]


def _text_coverage(text: str, expected_keywords: Sequence[str]) -> tuple[float, List[str]]:
    missing = [keyword for keyword in expected_keywords if not _contains_text(text, keyword)]
    return _coverage_score(expected_keywords, missing), missing


def _focus_area_coverage(
    markdown: str,
    actual_focus_areas: Sequence[str],
    expected_focus_areas: Sequence[str],
) -> tuple[float, List[str]]:
    actual = set(actual_focus_areas)
    missing = [
        focus
        for focus in expected_focus_areas
        if focus not in actual or not _contains_text(markdown, f"### {focus}")
    ]
    return _coverage_score(expected_focus_areas, missing), missing


def _citation_coverage(
    markdown: str,
    expected_sources: Sequence[str],
) -> tuple[float, List[str]]:
    if not expected_sources:
        has_citation_section = "## 5. 关联知识片段" in markdown
        return (0.0 if has_citation_section else 1.0), []

    missing = [source for source in expected_sources if source not in markdown]
    return _coverage_score(expected_sources, missing), missing


def _coverage_score(expected: Sequence[str], missing: Sequence[str]) -> float:
    if not expected:
        return 1.0
    return (len(expected) - len(missing)) / len(expected)


def _contains_text(text: str, expected: str) -> bool:
    return expected.casefold() in text.casefold()


def _aggregate_metrics(results: Sequence[TestDesignCaseResult]) -> Dict[str, float]:
    metric_names = [
        "requirement_coverage",
        "dimension_coverage",
        "citation_coverage",
        "non_empty_output",
        "overall_score",
    ]
    return {
        metric_name: _average(result.metrics[metric_name] for result in results)
        for metric_name in metric_names
    }


def _average(values: Sequence[float] | Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(float(value) for value in items) / len(items)


def _load_version(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return str(payload.get("version", "unknown"))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False

"""Helpers for discovering and summarizing test execution reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple
from xml.etree import ElementTree


DEFAULT_JUNIT_CANDIDATES = (
    Path("reports/junit.xml"),
    Path("reports/pytest-junit.xml"),
    Path("test-results/junit.xml"),
    Path("artifacts/junit.xml"),
)

DEFAULT_ALLURE_RESULTS_CANDIDATES = (
    Path("reports/allure-results"),
    Path("allure-results"),
)

DEFAULT_ALLURE_REPORT_CANDIDATES = (
    Path("reports/allure-report"),
    Path("allure-report"),
)


@dataclass(frozen=True)
class ReportArtifact:
    """A discovered test-report artifact on disk."""

    artifact_type: str
    label: str
    path: Path
    exists: bool
    detail: str


@dataclass(frozen=True)
class TestExecutionSummary:
    """A lightweight summary extracted from a JUnit XML report."""

    source_path: Path
    suite_name: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: float


def _resolve_candidate_paths(project_root: Path, candidates: Sequence[Path]) -> List[Path]:
    return [project_root / candidate for candidate in candidates]


def _count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for item in path.rglob(pattern) if item.is_file())


def _describe_artifact(artifact_type: str, path: Path) -> str:
    if not path.exists():
        return "Not found"

    if artifact_type == "junit_xml":
        return "Pytest JUnit XML summary source"

    if artifact_type == "allure_results":
        json_count = _count_files(path, "*.json")
        return f"{json_count} result files"

    if artifact_type == "allure_report":
        has_index = (path / "index.html").exists()
        return "Static HTML report ready" if has_index else "Directory detected"

    return "Detected"


def discover_report_artifacts(project_root: Path | str = ".") -> List[ReportArtifact]:
    """Discover common pytest and Allure report locations."""
    root = Path(project_root)
    artifacts: List[ReportArtifact] = []

    for path in _resolve_candidate_paths(root, DEFAULT_JUNIT_CANDIDATES):
        artifacts.append(
            ReportArtifact(
                artifact_type="junit_xml",
                label="Pytest JUnit XML",
                path=path,
                exists=path.exists(),
                detail=_describe_artifact("junit_xml", path),
            )
        )

    for path in _resolve_candidate_paths(root, DEFAULT_ALLURE_RESULTS_CANDIDATES):
        artifacts.append(
            ReportArtifact(
                artifact_type="allure_results",
                label="Allure Results",
                path=path,
                exists=path.exists(),
                detail=_describe_artifact("allure_results", path),
            )
        )

    for path in _resolve_candidate_paths(root, DEFAULT_ALLURE_REPORT_CANDIDATES):
        artifacts.append(
            ReportArtifact(
                artifact_type="allure_report",
                label="Allure HTML Report",
                path=path,
                exists=path.exists(),
                detail=_describe_artifact("allure_report", path),
            )
        )

    return artifacts


def get_default_junit_report_path(project_root: Path | str = ".") -> str:
    """Return the first existing JUnit path, or the primary default location."""
    artifacts = discover_report_artifacts(project_root)
    for artifact in artifacts:
        if artifact.artifact_type == "junit_xml" and artifact.exists:
            return str(artifact.path)
    return str(Path(project_root) / DEFAULT_JUNIT_CANDIDATES[0])


def _parse_int_attr(value: str | None) -> int:
    return int(value or 0)


def _parse_float_attr(value: str | None) -> float:
    return float(value or 0.0)


def _collect_suites(root: ElementTree.Element) -> List[ElementTree.Element]:
    if root.tag == "testsuite":
        return [root]
    if root.tag == "testsuites":
        return [suite for suite in root if suite.tag == "testsuite"]
    raise ValueError(f"Unsupported JUnit root tag: {root.tag}")


def parse_junit_xml(report_path: Path | str) -> TestExecutionSummary:
    """Parse a JUnit XML report into a lightweight execution summary."""
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"JUnit report not found: {path}")

    root = ElementTree.parse(path).getroot()
    suites = _collect_suites(root)
    if not suites:
        raise ValueError(f"No testsuite elements found in JUnit report: {path}")

    total = sum(_parse_int_attr(suite.attrib.get("tests")) for suite in suites)
    failures = sum(_parse_int_attr(suite.attrib.get("failures")) for suite in suites)
    errors = sum(_parse_int_attr(suite.attrib.get("errors")) for suite in suites)
    skipped = sum(_parse_int_attr(suite.attrib.get("skipped")) for suite in suites)
    duration = sum(_parse_float_attr(suite.attrib.get("time")) for suite in suites)

    if total == 0:
        total = sum(len(suite.findall(".//testcase")) for suite in suites)

    passed = max(total - failures - errors - skipped, 0)
    suite_name = root.attrib.get("name") or suites[0].attrib.get("name") or "pytest"

    return TestExecutionSummary(
        source_path=path,
        suite_name=suite_name,
        total=total,
        passed=passed,
        failed=failures,
        errors=errors,
        skipped=skipped,
        duration_seconds=duration,
    )


def load_execution_summary(
    report_path: str,
) -> Tuple[TestExecutionSummary | None, str | None]:
    """Parse a JUnit report path with a warning-oriented API for the dashboard."""
    candidate = report_path.strip()
    if not candidate:
        return None, "请输入 JUnit XML 报告路径。"

    try:
        summary = parse_junit_xml(candidate)
        return summary, None
    except FileNotFoundError:
        return None, "当前未找到 JUnit XML 报告。请先运行 pytest 并生成报告。"
    except Exception as exc:
        return None, f"无法解析测试报告：{exc}"

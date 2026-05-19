"""Traceability matrix between requirements, test points, and executions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from src.observability.dashboard.services.automation_scenario_service import (
    AutomationScenario,
    list_automation_scenarios,
)
from src.observability.dashboard.services.execution_history_service import (
    ExecutionHistoryRecord,
)


DIMENSION_ALIASES: Mapping[str, str] = {
    "功能": "功能",
    "functional": "功能",
    "boundary": "边界",
    "边界": "边界",
    "exception": "异常",
    "异常": "异常",
    "error": "异常",
    "security": "安全",
    "安全": "安全",
    "regression": "回归",
    "回归": "回归",
    "performance": "性能",
    "性能": "性能",
    "ui": "界面",
    "界面": "界面",
    "兼容": "兼容",
    "compatibility": "兼容",
    "易用": "易用",
    "usability": "易用",
    "弱网": "弱网",
    "network": "弱网",
    "并发": "并发",
    "concurrency": "并发",
}

DOMAIN_KEYWORDS = (
    "api",
    "allure",
    "auth",
    "browser",
    "ci",
    "http",
    "junit",
    "login",
    "rag",
    "token",
    "ui",
    "上传",
    "下游",
    "兼容",
    "冒烟",
    "分页",
    "历史",
    "召回",
    "告警",
    "回归",
    "密码",
    "并发",
    "性能",
    "执行",
    "接口",
    "搜索",
    "提示",
    "文件",
    "断网",
    "日志",
    "权限",
    "检索",
    "浏览器",
    "状态码",
    "用户",
    "用户名",
    "登录",
    "知识库",
    "测试",
    "界面",
    "认证",
    "评估",
    "账号",
    "账户",
    "超时",
    "越权",
    "输入",
    "错误",
    "错误码",
    "锁定",
    "页面",
)

STOPWORDS = {
    "and",
    "for",
    "from",
    "the",
    "with",
    "this",
    "that",
    "when",
    "then",
}

SCENARIO_EXTRA_KEYWORDS: Mapping[str, Sequence[str]] = {
    "api_login": ("api", "auth", "login", "token", "接口", "登录", "认证", "密码", "账号"),
    "api_file_upload": ("api", "upload", "接口", "上传", "文件", "二进制"),
    "ui_login_smoke": ("ui", "browser", "login", "页面", "表单", "登录", "浏览器", "冒烟"),
}


@dataclass(frozen=True)
class TraceabilityRequirement:
    """One requirement item extracted from user input."""

    requirement_id: str
    text: str
    keywords: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the requirement item."""
        return asdict(self)


@dataclass(frozen=True)
class TraceabilityTestPoint:
    """One test point extracted from a Markdown test design."""

    point_id: str
    dimension: str
    text: str
    keywords: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the test point."""
        return asdict(self)


@dataclass(frozen=True)
class TraceabilityAutomationLink:
    """Automation scenario coverage and latest execution status."""

    scenario_id: str
    name: str
    status: str
    latest_record_id: str = ""
    latest_created_at: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Serialize the automation link."""
        return asdict(self)


@dataclass(frozen=True)
class TraceabilityRow:
    """One matrix row for a requirement."""

    requirement_id: str
    requirement: str
    keywords: List[str]
    dimensions: List[str]
    test_points: List[TraceabilityTestPoint]
    automation: List[TraceabilityAutomationLink]
    latest_status: str
    risk_level: str
    gaps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the matrix row."""
        return {
            "requirement_id": self.requirement_id,
            "requirement": self.requirement,
            "keywords": self.keywords,
            "dimensions": self.dimensions,
            "test_points": [point.to_dict() for point in self.test_points],
            "automation": [link.to_dict() for link in self.automation],
            "latest_status": self.latest_status,
            "risk_level": self.risk_level,
            "gaps": self.gaps,
        }

    def to_row(self) -> Dict[str, str]:
        """Return a table-friendly row."""
        return {
            "Requirement ID": self.requirement_id,
            "Requirement": self.requirement,
            "Dimensions": ", ".join(self.dimensions) or "None",
            "Test Points": str(len(self.test_points)),
            "Automation": ", ".join(link.scenario_id for link in self.automation) or "None",
            "Latest Status": self.latest_status,
            "Risk": self.risk_level,
            "Gaps": "; ".join(self.gaps) or "None",
        }


@dataclass(frozen=True)
class TraceabilityReport:
    """Traceability matrix summary."""

    requirement_count: int
    covered_requirement_count: int
    automated_requirement_count: int
    passed_requirement_count: int
    rows: List[TraceabilityRow]

    @property
    def coverage_rate(self) -> float:
        """Return requirement coverage rate by test points."""
        return _ratio(self.covered_requirement_count, self.requirement_count)

    @property
    def automation_rate(self) -> float:
        """Return requirement automation-link rate."""
        return _ratio(self.automated_requirement_count, self.requirement_count)

    @property
    def passed_rate(self) -> float:
        """Return requirement passed-execution rate."""
        return _ratio(self.passed_requirement_count, self.requirement_count)

    def to_rows(self) -> List[Dict[str, str]]:
        """Return table-friendly rows."""
        return [row.to_row() for row in self.rows]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the traceability report."""
        return {
            "requirement_count": self.requirement_count,
            "covered_requirement_count": self.covered_requirement_count,
            "automated_requirement_count": self.automated_requirement_count,
            "passed_requirement_count": self.passed_requirement_count,
            "coverage_rate": self.coverage_rate,
            "automation_rate": self.automation_rate,
            "passed_rate": self.passed_rate,
            "rows": [row.to_dict() for row in self.rows],
        }


def build_traceability_report(
    requirement_text: str,
    test_design_markdown: str,
    execution_records: Iterable[ExecutionHistoryRecord] = (),
    scenarios: Sequence[AutomationScenario] | None = None,
) -> TraceabilityReport:
    """Build a deterministic requirements-to-test-to-execution matrix."""
    requirements = extract_requirement_items(requirement_text)
    test_points = extract_test_points(test_design_markdown)
    scenario_list = list(scenarios) if scenarios is not None else list_automation_scenarios()
    latest_records = _latest_record_by_scenario(execution_records)

    rows: List[TraceabilityRow] = []
    for requirement in requirements:
        matched_points = _match_test_points(requirement, test_points)
        matched_scenarios = _match_scenarios(requirement, matched_points, scenario_list)
        automation_links = [
            _build_automation_link(scenario, latest_records.get(scenario.scenario_id))
            for scenario in matched_scenarios
        ]
        dimensions = _unique(point.dimension for point in matched_points if point.dimension)
        latest_status = _summarize_latest_status(automation_links)
        gaps = _build_gaps(matched_points, automation_links, latest_status)
        rows.append(
            TraceabilityRow(
                requirement_id=requirement.requirement_id,
                requirement=requirement.text,
                keywords=requirement.keywords,
                dimensions=dimensions,
                test_points=matched_points,
                automation=automation_links,
                latest_status=latest_status,
                risk_level=_risk_level(gaps, latest_status),
                gaps=gaps,
            )
        )

    return TraceabilityReport(
        requirement_count=len(rows),
        covered_requirement_count=sum(1 for row in rows if row.test_points),
        automated_requirement_count=sum(1 for row in rows if row.automation),
        passed_requirement_count=sum(1 for row in rows if row.latest_status == "passed"),
        rows=rows,
    )


def extract_requirement_items(requirement_text: str) -> List[TraceabilityRequirement]:
    """Extract requirement items from lines, bullets, or short sentences."""
    candidates: List[str] = []
    for line in requirement_text.splitlines():
        cleaned = _clean_line_item(line)
        if cleaned:
            candidates.append(cleaned)

    if len(candidates) <= 1:
        candidates = [
            item.strip()
            for item in re.split(r"[。；;]+", requirement_text)
            if item.strip()
        ]

    requirements: List[TraceabilityRequirement] = []
    for index, item in enumerate(_unique(candidates)[:20], start=1):
        requirements.append(
            TraceabilityRequirement(
                requirement_id=f"REQ-{index:03d}",
                text=item,
                keywords=_extract_keywords(item),
            )
        )
    return requirements


def extract_test_points(markdown: str) -> List[TraceabilityTestPoint]:
    """Extract bullet test points from Markdown while preserving dimensions."""
    points: List[TraceabilityTestPoint] = []
    current_dimension = "通用"
    in_test_points_section = False

    for line in markdown.splitlines():
        stripped = line.strip()
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            title = heading.group(2).strip()
            heading_level = len(heading.group(1))
            if "测试点" in title or "test point" in title.lower():
                in_test_points_section = True
            elif in_test_points_section and heading_level <= 2:
                in_test_points_section = False

            dimension = _normalize_dimension(title)
            if dimension:
                current_dimension = dimension
            continue

        cleaned = _clean_bullet(stripped)
        if not cleaned:
            continue
        if not in_test_points_section:
            continue
        points.append(
            TraceabilityTestPoint(
                point_id=f"TP-{len(points) + 1:03d}",
                dimension=current_dimension,
                text=cleaned,
                keywords=_extract_keywords(cleaned),
            )
        )

    return points


def _match_test_points(
    requirement: TraceabilityRequirement,
    test_points: Sequence[TraceabilityTestPoint],
) -> List[TraceabilityTestPoint]:
    matched: List[TraceabilityTestPoint] = []
    for point in test_points:
        score = _overlap_score(requirement.keywords, point.keywords)
        if score >= 1 or _text_contains(requirement.text, point.text):
            matched.append(point)
    return matched[:8]


def _match_scenarios(
    requirement: TraceabilityRequirement,
    test_points: Sequence[TraceabilityTestPoint],
    scenarios: Sequence[AutomationScenario],
) -> List[AutomationScenario]:
    context_keywords = set(requirement.keywords)
    for point in test_points:
        context_keywords.update(point.keywords)

    matched: List[AutomationScenario] = []
    for scenario in scenarios:
        scenario_keywords = _scenario_keywords(scenario)
        score = _overlap_score(sorted(context_keywords), sorted(scenario_keywords))
        if score >= 2 or _has_strong_scenario_match(requirement.keywords, scenario):
            matched.append(scenario)
    return matched


def _build_automation_link(
    scenario: AutomationScenario,
    latest_record: ExecutionHistoryRecord | None,
) -> TraceabilityAutomationLink:
    if latest_record is None:
        return TraceabilityAutomationLink(
            scenario_id=scenario.scenario_id,
            name=scenario.name,
            status="not_run",
        )
    return TraceabilityAutomationLink(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        status=latest_record.status,
        latest_record_id=latest_record.record_id,
        latest_created_at=latest_record.created_at,
    )


def _build_gaps(
    test_points: Sequence[TraceabilityTestPoint],
    automation_links: Sequence[TraceabilityAutomationLink],
    latest_status: str,
) -> List[str]:
    gaps: List[str] = []
    if not test_points:
        gaps.append("missing_test_design")
    if not automation_links:
        gaps.append("missing_automation")
    elif latest_status == "not_run":
        gaps.append("automation_not_run")
    elif latest_status == "dry_run":
        gaps.append("only_dry_run")
    elif latest_status == "failed":
        gaps.append("latest_execution_failed")
    return gaps


def _risk_level(gaps: Sequence[str], latest_status: str) -> str:
    if "missing_test_design" in gaps or latest_status == "failed":
        return "high"
    if gaps:
        return "medium"
    return "low"


def _summarize_latest_status(automation_links: Sequence[TraceabilityAutomationLink]) -> str:
    if not automation_links:
        return "not_automated"
    statuses = [link.status for link in automation_links]
    if "failed" in statuses:
        return "failed"
    if "passed" in statuses:
        return "passed"
    if "dry_run" in statuses:
        return "dry_run"
    return "not_run"


def _latest_record_by_scenario(
    execution_records: Iterable[ExecutionHistoryRecord],
) -> Dict[str, ExecutionHistoryRecord]:
    latest: Dict[str, ExecutionHistoryRecord] = {}
    for record in execution_records:
        if not record.scenario_id:
            continue
        current = latest.get(record.scenario_id)
        if current is None or _parse_created_at(record.created_at) > _parse_created_at(
            current.created_at
        ):
            latest[record.scenario_id] = record
    return latest


def _scenario_keywords(scenario: AutomationScenario) -> set[str]:
    text = " ".join(
        [
            scenario.scenario_id,
            scenario.name,
            scenario.category,
            scenario.description,
            " ".join(scenario.labels),
            " ".join(SCENARIO_EXTRA_KEYWORDS.get(scenario.scenario_id, ())),
        ]
    )
    return set(_extract_keywords(text))


def _has_strong_scenario_match(
    requirement_keywords: Sequence[str],
    scenario: AutomationScenario,
) -> bool:
    keywords = set(requirement_keywords)
    if scenario.scenario_id == "api_login":
        return "登录" in keywords and ("接口" in keywords or "api" in keywords)
    if scenario.scenario_id == "api_file_upload":
        return "上传" in keywords and ("文件" in keywords or "接口" in keywords)
    if scenario.scenario_id == "ui_login_smoke":
        return "登录" in keywords and ("页面" in keywords or "ui" in keywords)
    return False


def _extract_keywords(text: str) -> List[str]:
    normalized = text.lower()
    keywords = {
        token
        for token in re.findall(r"[a-z0-9_]+", normalized)
        if len(token) >= 3 and token not in STOPWORDS
    }
    for keyword in DOMAIN_KEYWORDS:
        if keyword.lower() in normalized:
            keywords.add(keyword.lower())
    return sorted(keywords)


def _overlap_score(left: Sequence[str], right: Sequence[str]) -> int:
    return len(set(left) & set(right))


def _text_contains(left: str, right: str) -> bool:
    normalized_left = re.sub(r"\s+", "", left.lower())
    normalized_right = re.sub(r"\s+", "", right.lower())
    return bool(normalized_left) and (
        normalized_left in normalized_right or normalized_right in normalized_left
    )


def _normalize_dimension(title: str) -> str:
    normalized = title.strip().lower()
    for alias, dimension in DIMENSION_ALIASES.items():
        if alias.lower() in normalized:
            return dimension
    return ""


def _clean_bullet(line: str) -> str:
    if not re.match(r"^\s*(?:[-*+]|\d+[.)]|[a-zA-Z][.)])\s+", line):
        return ""
    return re.sub(r"^\s*(?:[-*+]|\d+[.)]|[a-zA-Z][.)])\s*", "", line).strip()


def _clean_line_item(line: str) -> str:
    return re.sub(r"^\s*(?:[-*+]|\d+[.)]|[a-zA-Z][.)])\s*", "", line).strip()


def _unique(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    unique_items: List[str] = []
    for item in items:
        normalized = re.sub(r"\s+", " ", str(item).strip())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_items.append(normalized)
    return unique_items


def _ratio(value: int, total: int) -> float:
    return round(value / total, 4) if total else 0.0


def _parse_created_at(value: str) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed

"""Deterministic review checks for generated test-design drafts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence


DEFAULT_EXPECTED_DIMENSIONS = (
    "functional",
    "boundary",
    "exception",
    "security",
    "regression",
)

DIMENSION_LABELS: Mapping[str, str] = {
    "functional": "功能测试",
    "boundary": "边界测试",
    "exception": "异常测试",
    "security": "安全测试",
    "regression": "回归测试",
    "performance": "性能测试",
    "ui": "界面测试",
    "compatibility": "兼容性测试",
    "usability": "易用性测试",
    "weak_network": "弱网测试",
    "concurrency": "并发测试",
}

DIMENSION_KEYWORDS: Mapping[str, Sequence[str]] = {
    "functional": ("功能", "主流程", "成功", "业务", "functional", "happy path"),
    "boundary": ("边界", "空值", "长度", "最大", "最小", "越界", "boundary", "limit"),
    "exception": ("异常", "失败", "错误", "超时", "不可用", "exception", "error", "timeout"),
    "security": ("安全", "权限", "越权", "token", "认证", "敏感", "security", "auth"),
    "regression": ("回归", "影响范围", "兼容旧", "regression"),
    "performance": ("性能", "响应时间", "吞吐", "qps", "tps", "latency", "performance"),
    "ui": ("界面", "页面", "按钮", "弹窗", "布局", "ui", "screen"),
    "compatibility": ("兼容", "浏览器", "移动端", "chrome", "firefox", "compatibility"),
    "usability": ("易用", "提示", "可读", "用户体验", "usability"),
    "weak_network": ("弱网", "断网", "重连", "丢包", "network"),
    "concurrency": ("并发", "重复提交", "锁", "concurrent", "race"),
}

VAGUE_PATTERNS = (
    "功能是否正常",
    "页面是否正常",
    "接口是否正常",
    "正常显示",
    "测试正常",
    "验证正常",
    "works well",
    "as expected",
    "normal",
)

UNTESTABLE_PATTERNS = (
    "体验良好",
    "页面美观",
    "简单易用",
    "性能良好",
    "合理",
    "友好",
    "稳定可靠",
    "good experience",
    "beautiful",
)

ASSERTION_HINTS = (
    "断言",
    "预期",
    "返回",
    "状态码",
    "错误码",
    "提示",
    "结果",
    "assert",
    "expect",
    "should",
    "status",
    "return",
    "returns",
    "http",
    "error code",
    "token",
    "schema",
    "rejected",
)


@dataclass(frozen=True)
class TestDesignReviewFinding:
    """One deterministic review finding."""

    finding_id: str
    severity: str
    category: str
    message: str
    suggestion: str
    evidence: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Serialize the finding."""
        return asdict(self)


@dataclass(frozen=True)
class TestDesignReviewReport:
    """Review result for one test-design markdown draft."""

    risk_level: str
    score: int
    covered_dimensions: List[str]
    missing_dimensions: List[str]
    findings: List[TestDesignReviewFinding]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the review report."""
        return {
            "risk_level": self.risk_level,
            "score": self.score,
            "covered_dimensions": self.covered_dimensions,
            "missing_dimensions": self.missing_dimensions,
            "findings": [finding.to_dict() for finding in self.findings],
        }

    def to_rows(self) -> List[Dict[str, str]]:
        """Return table-friendly finding rows."""
        return [
            {
                "Severity": finding.severity,
                "Category": finding.category,
                "Message": finding.message,
                "Suggestion": finding.suggestion,
                "Evidence": finding.evidence,
            }
            for finding in self.findings
        ]


def review_test_design_markdown(
    markdown: str,
    expected_dimensions: Sequence[str] = DEFAULT_EXPECTED_DIMENSIONS,
) -> TestDesignReviewReport:
    """Review a generated test-design draft with deterministic quality rules."""
    normalized = _normalize(markdown)
    findings: List[TestDesignReviewFinding] = []

    if not normalized:
        findings.append(
            TestDesignReviewFinding(
                finding_id="empty-draft",
                severity="high",
                category="completeness",
                message="测试设计草稿为空。",
                suggestion="先生成或补充功能、边界、异常、安全、回归等测试点。",
            )
        )
        return _build_report([], list(expected_dimensions), findings)

    covered_dimensions = [
        dimension for dimension in DIMENSION_LABELS if _contains_dimension(normalized, dimension)
    ]
    missing_dimensions = [
        dimension for dimension in expected_dimensions if dimension not in covered_dimensions
    ]

    for dimension in missing_dimensions:
        findings.append(
            TestDesignReviewFinding(
                finding_id=f"missing-{dimension}",
                severity="medium",
                category="coverage",
                message=f"缺少{DIMENSION_LABELS.get(dimension, dimension)}维度。",
                suggestion=f"补充{DIMENSION_LABELS.get(dimension, dimension)}的测试点、输入数据和预期结果。",
            )
        )

    vague_lines = _matching_lines(markdown, VAGUE_PATTERNS)
    for index, line in enumerate(vague_lines[:5], start=1):
        findings.append(
            TestDesignReviewFinding(
                finding_id=f"vague-{index}",
                severity="medium",
                category="executability",
                message="存在过于空泛的测试描述。",
                suggestion="把描述改成可执行步骤，并写清输入、操作和可验证的预期结果。",
                evidence=line,
            )
        )

    untestable_lines = _matching_lines(markdown, UNTESTABLE_PATTERNS)
    for index, line in enumerate(untestable_lines[:5], start=1):
        findings.append(
            TestDesignReviewFinding(
                finding_id=f"untestable-{index}",
                severity="medium",
                category="assertion",
                message="存在难以自动化断言的主观描述。",
                suggestion="改成可量化断言，例如状态码、字段值、页面文本、耗时阈值或错误提示。",
                evidence=line,
            )
        )

    test_point_lines = _test_point_lines(markdown)
    weak_assertions = [
        line for line in test_point_lines if not _contains_any(_normalize(line), ASSERTION_HINTS)
    ]
    if test_point_lines and len(weak_assertions) / len(test_point_lines) >= 0.6:
        findings.append(
            TestDesignReviewFinding(
                finding_id="weak-assertions",
                severity="low",
                category="assertion",
                message="多数测试点没有明确断言或预期结果。",
                suggestion="为每条核心测试点补充可验证结果，例如响应字段、页面文本、错误码或数据库状态。",
                evidence=weak_assertions[0],
            )
        )

    if "引用" not in markdown and "source" not in normalized and "evidence" not in normalized:
        findings.append(
            TestDesignReviewFinding(
                finding_id="missing-evidence",
                severity="low",
                category="traceability",
                message="未看到需求、接口文档、缺陷或规范引用。",
                suggestion="补充测试依据来源，便于评审时追溯为什么要测这些场景。",
            )
        )

    return _build_report(covered_dimensions, missing_dimensions, findings)


def _build_report(
    covered_dimensions: Sequence[str],
    missing_dimensions: Sequence[str],
    findings: Sequence[TestDesignReviewFinding],
) -> TestDesignReviewReport:
    high_count = sum(1 for finding in findings if finding.severity == "high")
    medium_count = sum(1 for finding in findings if finding.severity == "medium")
    low_count = sum(1 for finding in findings if finding.severity == "low")
    score = max(0, 100 - high_count * 30 - medium_count * 12 - low_count * 5)

    if high_count or score < 60:
        risk_level = "high"
    elif medium_count or score < 85:
        risk_level = "medium"
    else:
        risk_level = "low"

    return TestDesignReviewReport(
        risk_level=risk_level,
        score=score,
        covered_dimensions=list(covered_dimensions),
        missing_dimensions=list(missing_dimensions),
        findings=list(findings),
    )


def _contains_dimension(text: str, dimension: str) -> bool:
    return _contains_any(text, DIMENSION_KEYWORDS.get(dimension, (dimension,)))


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    return any(_normalize(pattern) in text for pattern in patterns)


def _matching_lines(markdown: str, patterns: Iterable[str]) -> List[str]:
    matches: List[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped and _contains_any(_normalize(stripped), patterns):
            matches.append(stripped)
    return matches


def _test_point_lines(markdown: str) -> List[str]:
    return [
        line.strip()
        for line in markdown.splitlines()
        if re.match(r"^\s*(?:[-*]|\d+[.)])\s+", line)
    ]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

#!/usr/bin/env python
"""Run deterministic test-design evaluation for the AI test platform.

Usage:
    python scripts/evaluate_test_design.py
    python scripts/evaluate_test_design.py --json
    python scripts/evaluate_test_design.py --output data/evaluation/test_design_report.json
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.observability.dashboard.services.test_design_evaluation_service import (  # noqa: E402
    DEFAULT_TEST_DESIGN_GOLDEN_SET,
    run_test_design_evaluation,
    write_test_design_evaluation_report,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run deterministic evaluation for generated test-design drafts."
    )
    parser.add_argument(
        "--test-set",
        default=str(DEFAULT_TEST_DESIGN_GOLDEN_SET),
        help="Path to test-design Golden Test Set JSON.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional report path. Must be under data/evaluation/ when provided.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full report as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    """Run test-design evaluation and optionally write a report."""
    args = parse_args()

    try:
        report = run_test_design_evaluation(args.test_set)
        if args.output:
            written_path = write_test_design_evaluation_report(
                report,
                args.output,
                project_root=PROJECT_ROOT,
            )
            print(f"Report written: {written_path}")

        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            _print_report(report)
    except Exception as exc:
        print(f"Test-design evaluation failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _print_report(report) -> None:
    """Print a compact text report."""
    print("=" * 72)
    print("  TEST DESIGN EVALUATION REPORT")
    print("=" * 72)
    print(f"  Test Set: {report.test_set_path}")
    print(f"  Version:  {report.version}")
    print(f"  Cases:    {report.case_count}")
    print(f"  Time:     {report.total_elapsed_ms:.0f} ms")
    print()

    print("Aggregate metrics")
    for name, value in sorted(report.aggregate_metrics.items()):
        print(f"  {name:<24s} {value:.4f}")
    print()

    print("Case results")
    for result in report.case_results:
        metrics = result.metrics
        print(
            f"  - {result.case_id}: overall={metrics['overall_score']:.4f}, "
            f"requirement={metrics['requirement_coverage']:.4f}, "
            f"dimension={metrics['dimension_coverage']:.4f}, "
            f"citation={metrics['citation_coverage']:.4f}, "
            f"non_empty={metrics['non_empty_output']:.4f}"
        )
        if result.missing_keywords:
            print(f"    missing keywords: {', '.join(result.missing_keywords)}")
        if result.missing_focus_areas:
            print(f"    missing focus areas: {', '.join(result.missing_focus_areas)}")
        if result.missing_citation_sources:
            print(f"    missing citations: {', '.join(result.missing_citation_sources)}")
    print("=" * 72)


if __name__ == "__main__":
    sys.exit(main())

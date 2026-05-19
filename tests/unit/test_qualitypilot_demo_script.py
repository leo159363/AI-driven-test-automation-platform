"""Tests for the QualityPilot end-to-end demo script."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_qualitypilot_demo import run_demo


@pytest.mark.asyncio
async def test_run_qualitypilot_demo_generates_artifacts(tmp_path: Path) -> None:
    summary = await run_demo(output_dir=tmp_path)

    assert summary["headline"]["execution_status"] == "failed"
    assert summary["headline"]["report_status"] == "failed"
    assert summary["headline"]["failed_case_count"] == 1
    assert summary["headline"]["bug_count"] == 1

    outputs = summary["outputs"]
    assert Path(outputs["junitxml"]).exists()
    assert Path(outputs["allure_results"]).exists()
    assert (tmp_path / "demo_summary.json").exists()
    assert (tmp_path / "bug_report.md").exists()

    persisted = json.loads((tmp_path / "demo_summary.json").read_text(encoding="utf-8"))
    assert persisted["headline"]["bug_count"] == 1
    assert "generate_bug_report" in persisted["workflow"]
    assert "# [auth]" in (tmp_path / "bug_report.md").read_text(encoding="utf-8")

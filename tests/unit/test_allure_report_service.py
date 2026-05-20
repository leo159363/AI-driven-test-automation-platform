"""Tests for Allure HTML generation helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.observability.dashboard.services.allure_report_service import (
    build_allure_generate_command,
    generate_allure_html_report,
)


def test_build_allure_generate_command_defaults_to_clean() -> None:
    command = build_allure_generate_command("results", "html")

    assert command == ["allure", "generate", "results", "-o", "html", "--clean"]


def test_generate_allure_html_report_returns_missing_results(tmp_path: Path) -> None:
    result = generate_allure_html_report(
        results_dir=tmp_path / "missing-results",
        output_dir=tmp_path / "allure-report",
    )

    assert result.status == "missing_results"
    assert result.exit_code is None
    assert "not found" in result.message


def test_generate_allure_html_report_returns_empty_results(tmp_path: Path) -> None:
    results_dir = tmp_path / "allure-results"
    results_dir.mkdir()

    result = generate_allure_html_report(
        results_dir=results_dir,
        output_dir=tmp_path / "allure-report",
    )

    assert result.status == "empty_results"
    assert "No Allure result JSON" in result.message


def test_generate_allure_html_report_returns_missing_cli(tmp_path: Path, monkeypatch) -> None:
    results_dir = tmp_path / "allure-results"
    results_dir.mkdir()
    (results_dir / "case-result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "src.observability.dashboard.services.allure_report_service.shutil.which",
        lambda executable: None,
    )

    result = generate_allure_html_report(
        results_dir=results_dir,
        output_dir=tmp_path / "allure-report",
    )

    assert result.status == "missing_cli"
    assert "not installed" in result.message


def test_generate_allure_html_report_success(tmp_path: Path, monkeypatch) -> None:
    results_dir = tmp_path / "allure-results"
    output_dir = tmp_path / "allure-report"
    results_dir.mkdir()
    (results_dir / "case-result.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        "src.observability.dashboard.services.allure_report_service.shutil.which",
        lambda executable: "fake-allure",
    )

    def fake_run(command, check, capture_output, text, timeout):
        assert command[:2] == ["fake-allure", "generate"]
        output_dir.mkdir(parents=True)
        (output_dir / "index.html").write_text("<html></html>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="generated", stderr="")

    monkeypatch.setattr(
        "src.observability.dashboard.services.allure_report_service.subprocess.run",
        fake_run,
    )

    result = generate_allure_html_report(results_dir=results_dir, output_dir=output_dir)

    assert result.status == "generated"
    assert result.exit_code == 0
    assert result.index_path == output_dir / "index.html"
    assert result.to_dict()["index_path"] == str(output_dir / "index.html")


def test_generate_allure_html_report_failed_cli(tmp_path: Path, monkeypatch) -> None:
    results_dir = tmp_path / "allure-results"
    output_dir = tmp_path / "allure-report"
    results_dir.mkdir()
    (results_dir / "case-result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "src.observability.dashboard.services.allure_report_service.shutil.which",
        lambda executable: "fake-allure",
    )
    monkeypatch.setattr(
        "src.observability.dashboard.services.allure_report_service.subprocess.run",
        lambda command, check, capture_output, text, timeout: subprocess.CompletedProcess(
            command,
            2,
            stdout="",
            stderr="boom",
        ),
    )

    result = generate_allure_html_report(results_dir=results_dir, output_dir=output_dir)

    assert result.status == "failed"
    assert result.exit_code == 2
    assert result.stderr == "boom"

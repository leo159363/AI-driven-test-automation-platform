"""Unit tests for FastAPI automation run service."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.api.services import automation_run_service as service


def _write_junit(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="api" tests="2" failures="0" errors="0" skipped="0" time="0.2">
  <testcase classname="api" name="test_one" time="0.1" />
  <testcase classname="api" name="test_two" time="0.1" />
</testsuite>
""",
        encoding="utf-8",
    )


def test_run_automation_scenario_writes_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        command = args[0]
        junit_index = command.index("--junitxml") + 1
        _write_junit(tmp_path / command[junit_index])
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(service.subprocess, "run", fake_run)

    record = service.run_automation_scenario("api_login", project_root=tmp_path)

    assert record["scenario_id"] == "api_login"
    assert record["status"] == "passed"
    assert record["summary"]["total"] == 2
    assert (tmp_path / record["paths"]["run_record"]).exists()


def test_list_and_get_automation_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        command = args[0]
        junit_index = command.index("--junitxml") + 1
        _write_junit(tmp_path / command[junit_index])
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(service.subprocess, "run", fake_run)
    created = service.run_automation_scenario("api_file_upload", project_root=tmp_path)

    runs = service.list_automation_runs(tmp_path)
    loaded = service.get_automation_run(created["run_id"], tmp_path)

    assert runs[0]["run_id"] == created["run_id"]
    assert loaded["scenario_id"] == "api_file_upload"


def test_get_automation_run_rejects_missing_run(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        service.get_automation_run("not-found", tmp_path)

"""Execution history records for adapter runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping
from uuid import uuid4

from src.observability.dashboard.services.api_execution_adapter import ExecutionResult


DEFAULT_EXECUTION_HISTORY_PATH = Path("data/execution_history/records.jsonl")


@dataclass(frozen=True)
class ExecutionHistoryRecord:
    """A persisted summary of one execution adapter run."""

    record_id: str
    created_at: str
    plan_name: str
    adapter: str
    status: str
    base_url: str
    dry_run: bool
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    dry_run_steps: int
    duration_ms: float
    failure_reason: str = ""
    scenario_id: str = ""
    trigger: str = "manual"
    artifacts: Dict[str, str] = field(default_factory=dict)
    report_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the history record."""
        return asdict(self)

    def to_row(self) -> Dict[str, str]:
        """Return a table-friendly row."""
        return {
            "Created": self.created_at,
            "Plan": self.plan_name,
            "Scenario": self.scenario_id,
            "Adapter": self.adapter,
            "Status": self.status,
            "Steps": str(self.total_steps),
            "Passed": str(self.passed_steps),
            "Failed": str(self.failed_steps),
            "Skipped": str(self.skipped_steps + self.dry_run_steps),
            "Trigger": self.trigger,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExecutionHistoryRecord":
        """Deserialize a record and tolerate missing optional fields."""
        return cls(
            record_id=str(payload.get("record_id", "")),
            created_at=str(payload.get("created_at", "")),
            plan_name=str(payload.get("plan_name", "")),
            adapter=str(payload.get("adapter", "")),
            status=str(payload.get("status", "")),
            base_url=str(payload.get("base_url", "")),
            dry_run=bool(payload.get("dry_run", False)),
            total_steps=int(payload.get("total_steps", 0)),
            passed_steps=int(payload.get("passed_steps", 0)),
            failed_steps=int(payload.get("failed_steps", 0)),
            skipped_steps=int(payload.get("skipped_steps", 0)),
            dry_run_steps=int(payload.get("dry_run_steps", 0)),
            duration_ms=float(payload.get("duration_ms", 0.0)),
            failure_reason=str(payload.get("failure_reason", "")),
            scenario_id=str(payload.get("scenario_id", "")),
            trigger=str(payload.get("trigger", "manual")),
            artifacts=dict(payload.get("artifacts", {}) or {}),
            report_paths=dict(payload.get("report_paths", {}) or {}),
        )


def build_execution_history_record(
    result: ExecutionResult,
    scenario_id: str = "",
    trigger: str = "manual",
    report_paths: Mapping[str, str] | None = None,
) -> ExecutionHistoryRecord:
    """Build a persistent history summary from an execution result."""
    duration_ms = sum(step.elapsed_ms for step in result.step_results)
    return ExecutionHistoryRecord(
        record_id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        plan_name=result.plan_name,
        adapter=result.adapter,
        status=result.status,
        base_url=result.base_url,
        dry_run=result.dry_run,
        total_steps=result.total_steps,
        passed_steps=result.passed_steps,
        failed_steps=result.failed_steps,
        skipped_steps=result.skipped_steps,
        dry_run_steps=result.dry_run_steps,
        duration_ms=duration_ms,
        failure_reason=result.failure_reason or "",
        scenario_id=scenario_id,
        trigger=trigger,
        artifacts=dict(result.artifacts),
        report_paths=dict(report_paths or {}),
    )


def append_execution_history_record(
    record: ExecutionHistoryRecord,
    history_path: str | Path = DEFAULT_EXECUTION_HISTORY_PATH,
) -> Path:
    """Append a history record to JSONL storage and return the file path."""
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True))
        file.write("\n")
    return path


def load_execution_history_records(
    history_path: str | Path = DEFAULT_EXECUTION_HISTORY_PATH,
    limit: int = 100,
) -> List[ExecutionHistoryRecord]:
    """Load history records newest first."""
    path = Path(history_path)
    if not path.exists():
        return []

    records: List[ExecutionHistoryRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        records.append(ExecutionHistoryRecord.from_dict(json.loads(stripped)))

    records.reverse()
    if limit > 0:
        return records[:limit]
    return records


def summarize_execution_history(records: Iterable[ExecutionHistoryRecord]) -> Dict[str, int]:
    """Return aggregate counts for dashboard metrics."""
    snapshot = list(records)
    return {
        "total": len(snapshot),
        "passed": sum(1 for record in snapshot if record.status == "passed"),
        "failed": sum(1 for record in snapshot if record.status == "failed"),
        "dry_run": sum(1 for record in snapshot if record.status == "dry_run"),
    }

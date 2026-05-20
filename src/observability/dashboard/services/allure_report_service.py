"""Allure HTML report generation helpers."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ALLURE_RESULTS_DIR = Path("reports/qualitypilot-demo/allure-results")
DEFAULT_ALLURE_REPORT_DIR = Path("reports/qualitypilot-demo/allure-report")


@dataclass(frozen=True)
class AllureGenerationResult:
    """Structured result returned after trying to generate an Allure HTML report."""

    status: str
    results_dir: Path
    output_dir: Path
    command: list[str]
    exit_code: int | None = None
    index_path: Path | None = None
    message: str = ""
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly representation."""
        return {
            "status": self.status,
            "results_dir": str(self.results_dir),
            "output_dir": str(self.output_dir),
            "index_path": str(self.index_path) if self.index_path else "",
            "command": self.command,
            "exit_code": self.exit_code,
            "message": self.message,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def build_allure_generate_command(
    results_dir: str | Path = DEFAULT_ALLURE_RESULTS_DIR,
    output_dir: str | Path = DEFAULT_ALLURE_REPORT_DIR,
    clean: bool = True,
    allure_executable: str = "allure",
) -> list[str]:
    """Build the command used to generate a static Allure HTML report."""
    command = [
        allure_executable,
        "generate",
        str(Path(results_dir)),
        "-o",
        str(Path(output_dir)),
    ]
    if clean:
        command.append("--clean")
    return command


def generate_allure_html_report(
    results_dir: str | Path = DEFAULT_ALLURE_RESULTS_DIR,
    output_dir: str | Path = DEFAULT_ALLURE_REPORT_DIR,
    clean: bool = True,
    allure_executable: str = "allure",
    timeout_seconds: int = 120,
) -> AllureGenerationResult:
    """Generate a static Allure HTML report when the Allure CLI is available.

    The function is intentionally defensive: missing result files or a missing
    Allure CLI returns a structured status instead of raising, so the Dashboard
    can display actionable guidance.
    """
    results_path = Path(results_dir)
    output_path = Path(output_dir)
    command = build_allure_generate_command(
        results_dir=results_path,
        output_dir=output_path,
        clean=clean,
        allure_executable=allure_executable,
    )

    if not results_path.exists() or not results_path.is_dir():
        return AllureGenerationResult(
            status="missing_results",
            results_dir=results_path,
            output_dir=output_path,
            command=command,
            message=f"Allure results directory not found: {results_path}",
        )

    if not _has_allure_result_files(results_path):
        return AllureGenerationResult(
            status="empty_results",
            results_dir=results_path,
            output_dir=output_path,
            command=command,
            message=f"No Allure result JSON files found under: {results_path}",
        )

    resolved_executable = shutil.which(allure_executable)
    if not resolved_executable:
        return AllureGenerationResult(
            status="missing_cli",
            results_dir=results_path,
            output_dir=output_path,
            command=command,
            message=(
                "Allure CLI is not installed or not in PATH. Install Allure commandline, "
                "then rerun the same command."
            ),
        )

    command = build_allure_generate_command(
        results_dir=results_path,
        output_dir=output_path,
        clean=clean,
        allure_executable=resolved_executable,
    )

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return AllureGenerationResult(
            status="timeout",
            results_dir=results_path,
            output_dir=output_path,
            command=command,
            message=f"Allure generation timed out after {timeout_seconds} seconds.",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        )
    except OSError as exc:
        return AllureGenerationResult(
            status="failed",
            results_dir=results_path,
            output_dir=output_path,
            command=command,
            message=f"Failed to execute Allure CLI: {exc}",
        )

    index_path = output_path / "index.html"
    if completed.returncode != 0:
        return AllureGenerationResult(
            status="failed",
            results_dir=results_path,
            output_dir=output_path,
            command=command,
            exit_code=completed.returncode,
            index_path=index_path if index_path.exists() else None,
            message="Allure CLI returned a non-zero exit code.",
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    status = "generated" if index_path.exists() else "generated_without_index"
    message = (
        f"Allure HTML report generated: {index_path}"
        if status == "generated"
        else f"Allure CLI finished, but index.html was not found under: {output_path}"
    )
    return AllureGenerationResult(
        status=status,
        results_dir=results_path,
        output_dir=output_path,
        command=command,
        exit_code=completed.returncode,
        index_path=index_path if index_path.exists() else None,
        message=message,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _has_allure_result_files(results_path: Path) -> bool:
    return any(path.is_file() and path.suffix == ".json" for path in results_path.rglob("*"))

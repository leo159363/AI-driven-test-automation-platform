"""Generate a static Allure HTML report from local Allure results."""

from __future__ import annotations

import argparse
import json

from src.observability.dashboard.services.allure_report_service import (
    DEFAULT_ALLURE_REPORT_DIR,
    DEFAULT_ALLURE_RESULTS_DIR,
    generate_allure_html_report,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Allure HTML report.")
    parser.add_argument(
        "--results-dir",
        default=str(DEFAULT_ALLURE_RESULTS_DIR),
        help="Allure results directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_ALLURE_REPORT_DIR),
        help="Output directory for the static Allure HTML report.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not pass --clean to allure generate.",
    )
    parser.add_argument(
        "--allure-executable",
        default="allure",
        help="Allure CLI executable name or path.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Allure CLI timeout.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full structured result as JSON.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = generate_allure_html_report(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        clean=not args.no_clean,
        allure_executable=args.allure_executable,
        timeout_seconds=args.timeout_seconds,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"status={result.status}")
        print(f"message={result.message}")
        print(f"results_dir={result.results_dir}")
        print(f"output_dir={result.output_dir}")
        if result.index_path:
            print(f"index_path={result.index_path}")
        print("command=" + " ".join(result.command))

    return 0 if result.status in {"generated", "generated_without_index"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

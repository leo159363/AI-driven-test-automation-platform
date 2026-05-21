r"""Start the QualityPilot FastAPI backend and Vue frontend together.

Usage:
    .\.venv\Scripts\python.exe scripts\start_fullstack.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend" / "qualitypilot-web"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start QualityPilot full-stack dev servers.")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-port", type=int, default=5173)
    parser.add_argument("--host", default="127.0.0.1")
    return parser


def _npm_command() -> str:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise RuntimeError("npm was not found. Please install Node.js first.")
    return npm


def _start_fastapi(host: str, port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.main:app",
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=REPO_ROOT,
    )


def _start_vue(host: str, port: int) -> subprocess.Popen:
    if not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError(
            "frontend dependencies are missing. Run: cd frontend\\qualitypilot-web && npm.cmd install"
        )

    return subprocess.Popen(
        [_npm_command(), "run", "dev", "--", "--host", host, "--port", str(port)],
        cwd=FRONTEND_DIR,
    )


def _url_ok(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return 200 <= response.status < 500
    except URLError:
        return False
    except OSError:
        return False


def main() -> int:
    args = _parser().parse_args()
    processes: list[subprocess.Popen] = []

    try:
        api_health_url = f"http://{args.host}:{args.api_port}/api/health"
        web_url = f"http://{args.host}:{args.web_port}"

        if _url_ok(api_health_url):
            print(f"FastAPI already running: {api_health_url}")
        else:
            processes.append(_start_fastapi(args.host, args.api_port))
            time.sleep(1)

        if _url_ok(web_url):
            print(f"Vue frontend already running: {web_url}")
        else:
            processes.append(_start_vue(args.host, args.web_port))

        print("QualityPilot full-stack dev servers started")
        print(f"FastAPI docs: http://{args.host}:{args.api_port}/docs")
        print(f"Vue frontend: http://{args.host}:{args.web_port}")
        print("Press Ctrl+C to stop both servers.")

        while not processes or all(process.poll() is None for process in processes):
            time.sleep(1)

        return next((process.returncode or 0 for process in processes if process.poll() is not None), 0)
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()


if __name__ == "__main__":
    raise SystemExit(main())

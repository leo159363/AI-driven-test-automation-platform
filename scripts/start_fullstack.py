r"""Start the QualityPilot FastAPI backend and Vue frontend together.

Usage:
    .\.venv\Scripts\python.exe scripts\start_fullstack.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
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
            "--reload",
        ],
        cwd=REPO_ROOT,
    )


def _start_vue(host: str, port: int, api_url: str) -> subprocess.Popen:
    if not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError(
            "frontend dependencies are missing. Run: cd frontend\\qualitypilot-web && npm.cmd install"
        )

    env = os.environ.copy()
    env["VITE_API_PROXY_TARGET"] = api_url
    return subprocess.Popen(
        [_npm_command(), "run", "dev", "--", "--host", host, "--port", str(port)],
        cwd=FRONTEND_DIR,
        env=env,
    )


def _http_status_ok(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return 200 <= response.status < 400
    except (HTTPError, URLError):
        return False
    except OSError:
        return False


def _qualitypilot_api_ok(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return _is_qualitypilot_health_payload(payload)
    except (HTTPError, URLError, OSError, json.JSONDecodeError):
        return False


def _qualitypilot_api_routes_ok(api_base_url: str) -> bool:
    base_url = api_base_url.rstrip("/")
    required_routes = [
        "/api/api-testing/collections",
        "/api/settings/platform-configs",
    ]
    return all(_http_status_ok(f"{base_url}{route}") for route in required_routes)


def _qualitypilot_web_proxy_ok(web_url: str) -> bool:
    return _qualitypilot_api_ok(f"{web_url.rstrip('/')}/api/health")


def _is_qualitypilot_health_payload(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    return payload.get("status") == "ok" and payload.get("service") == "qualitypilot-api"


def _wait_for(predicate, process: subprocess.Popen | None = None, timeout_seconds: float = 12) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        if process is not None and process.poll() is not None:
            return False
        time.sleep(0.4)
    return False


def main() -> int:
    args = _parser().parse_args()
    processes: list[subprocess.Popen] = []

    try:
        api_health_url = f"http://{args.host}:{args.api_port}/api/health"
        api_base_url = f"http://{args.host}:{args.api_port}"
        web_url = f"http://{args.host}:{args.web_port}"

        if _qualitypilot_api_ok(api_health_url):
            if not _qualitypilot_api_routes_ok(api_base_url):
                raise RuntimeError(
                    f"FastAPI is already running on port {args.api_port}, "
                    "but /api/api-testing/collections is missing. "
                    "This usually means an old backend process is still running. "
                    "Stop the old terminal process, then rerun this script."
                )
            print(f"FastAPI already running: {api_health_url}")
        else:
            api_process = _start_fastapi(args.host, args.api_port)
            processes.append(api_process)
            if not _wait_for(
                lambda: _qualitypilot_api_ok(api_health_url)
                and _qualitypilot_api_routes_ok(api_base_url),
                api_process,
            ):
                raise RuntimeError(
                    "FastAPI did not start correctly. "
                    f"Check whether port {args.api_port} is occupied by another service, "
                    "or rerun with --api-port 8010."
                )

        if _http_status_ok(web_url):
            if not _qualitypilot_web_proxy_ok(web_url):
                raise RuntimeError(
                    f"Port {args.web_port} already has a web server, "
                    "but its /api proxy is not connected to QualityPilot FastAPI. "
                    "Close the old Vue terminal, or rerun with --web-port 5174."
                )
            print(f"Vue frontend already running: {web_url}")
        else:
            web_process = _start_vue(args.host, args.web_port, api_base_url)
            processes.append(web_process)
            if not _wait_for(
                lambda: _http_status_ok(web_url) and _qualitypilot_web_proxy_ok(web_url),
                web_process,
            ):
                raise RuntimeError(
                    "Vue frontend did not start correctly. "
                    f"Check whether port {args.web_port} is occupied by another service, "
                    "or rerun with --web-port 5174."
                )

        print("QualityPilot full-stack dev servers started")
        print(f"FastAPI docs: http://{args.host}:{args.api_port}/docs")
        print(f"Vue frontend: http://{args.host}:{args.web_port}")
        print(f"Vue /api proxy target: {api_base_url}")
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

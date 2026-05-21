"""Controlled API debug runner for the Vue API testing page."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class JsonAssertion:
    """One JSON response assertion."""

    path: str
    operator: str
    expected: Any = None


def run_api_debug_request(
    *,
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: str = "",
    base_url: str = "",
    expected_status: int | None = None,
    json_assertions: list[dict[str, Any]] | None = None,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    """Run one controlled API debug request and evaluate basic assertions."""
    normalized_method = _validate_method(method)
    normalized_path = _validate_path(path)
    normalized_headers = _normalize_headers(headers or {})
    started = time.perf_counter()

    if base_url.strip():
        response = _send_local_http_request(
            method=normalized_method,
            base_url=base_url,
            path=normalized_path,
            headers=normalized_headers,
            body=body,
            timeout_seconds=timeout_seconds,
        )
        target_mode = "local_http"
    else:
        response = _send_mock_request(
            method=normalized_method,
            path=normalized_path,
            headers=normalized_headers,
            body=body,
        )
        target_mode = "mock"

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    assertion_results = _evaluate_assertions(
        status_code=int(response["status_code"]),
        json_body=response.get("json"),
        expected_status=expected_status,
        json_assertions=json_assertions or [],
    )
    passed = all(item["passed"] for item in assertion_results)

    return {
        "request": {
            "method": normalized_method,
            "path": normalized_path,
            "base_url": base_url.strip(),
            "headers": normalized_headers,
            "body": body,
            "target_mode": target_mode,
        },
        "response": {
            **response,
            "duration_ms": duration_ms,
        },
        "assertions": assertion_results,
        "passed": passed,
        "summary": {
            "total": len(assertion_results),
            "passed": sum(1 for item in assertion_results if item["passed"]),
            "failed": sum(1 for item in assertion_results if not item["passed"]),
        },
    }


def _send_mock_request(
    *,
    method: str,
    path: str,
    headers: dict[str, str],
    body: str,
) -> dict[str, Any]:
    payload = _parse_json_body(body)
    if method == "POST" and path == "/api/login":
        username = str(payload.get("username", "") if isinstance(payload, dict) else "")
        password = str(payload.get("password", "") if isinstance(payload, dict) else "")
        if not username or not password:
            return _json_response(400, {"error": "missing_required_field"})
        if username == "tester" and password == "Passw0rd!":
            return _json_response(200, {"token": "demo-token", "user": {"username": username}})
        return _json_response(401, {"error": "invalid_credentials"})

    if method == "POST" and path == "/api/upload":
        filename = headers.get("X-Filename") or headers.get("x-filename")
        if not filename:
            return _json_response(400, {"error": "missing_filename"})
        return _json_response(201, {"filename": filename, "size": len(body.encode("utf-8"))})

    return _json_response(404, {"error": "not_found", "path": path})


def _send_local_http_request(
    *,
    method: str,
    base_url: str,
    path: str,
    headers: dict[str, str],
    body: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    parsed = urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("base_url must start with http:// or https://")
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("Only localhost targets are allowed for API debugging")

    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    data = body.encode("utf-8") if method not in {"GET", "DELETE"} else None
    request = Request(url=url, method=method, data=data, headers=headers)
    try:
        with urlopen(request, timeout=max(1, min(int(timeout_seconds or 10), 30))) as response:
            raw = response.read()
            status_code = response.status
            response_headers = dict(response.headers.items())
    except HTTPError as exc:
        raw = exc.read()
        status_code = exc.code
        response_headers = dict(exc.headers.items())
    except URLError as exc:
        raise ValueError(f"HTTP request failed: {exc.reason}") from exc

    text = raw.decode("utf-8", errors="replace")
    json_body = _try_json(text)
    return {
        "status_code": status_code,
        "headers": response_headers,
        "body": text,
        "json": json_body,
    }


def _evaluate_assertions(
    *,
    status_code: int,
    json_body: Any,
    expected_status: int | None,
    json_assertions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if expected_status is not None:
        results.append(
            {
                "type": "status_code",
                "name": f"status == {expected_status}",
                "passed": status_code == int(expected_status),
                "actual": status_code,
                "expected": expected_status,
            }
        )

    for item in json_assertions:
        assertion = JsonAssertion(
            path=str(item.get("path", "")).strip(),
            operator=str(item.get("operator", "equals")).strip() or "equals",
            expected=item.get("expected"),
        )
        results.append(_evaluate_json_assertion(json_body, assertion))
    return results


def _evaluate_json_assertion(json_body: Any, assertion: JsonAssertion) -> dict[str, Any]:
    exists, actual = _get_json_path(json_body, assertion.path)
    operator = assertion.operator
    expected = assertion.expected
    if operator == "exists":
        passed = exists
    elif operator == "not_exists":
        passed = not exists
    elif operator == "contains":
        passed = exists and str(expected) in str(actual)
    elif operator == "equals":
        passed = exists and str(actual) == str(expected)
    else:
        raise ValueError(f"Unsupported assertion operator: {operator}")

    return {
        "type": "json_path",
        "name": f"{assertion.path} {operator} {expected}",
        "path": assertion.path,
        "operator": operator,
        "passed": passed,
        "actual": actual if exists else None,
        "expected": expected,
    }


def _get_json_path(payload: Any, path: str) -> tuple[bool, Any]:
    if not path:
        return False, None
    current = payload
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
            continue
        return False, None
    return True, current


def _validate_method(method: str) -> str:
    normalized = (method or "").strip().upper()
    if normalized not in ALLOWED_HTTP_METHODS:
        allowed = ", ".join(sorted(ALLOWED_HTTP_METHODS))
        raise ValueError(f"Unsupported HTTP method: {method}. Available: {allowed}")
    return normalized


def _validate_path(path: str) -> str:
    normalized = (path or "").strip()
    if not normalized.startswith("/"):
        raise ValueError("path must start with /")
    return normalized


def _normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {str(key).strip(): str(value) for key, value in headers.items() if str(key).strip()}


def _parse_json_body(body: str) -> Any:
    if not body.strip():
        return {}
    parsed = _try_json(body)
    return parsed if parsed is not None else {}


def _try_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _json_response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, ensure_ascii=False),
        "json": payload,
    }

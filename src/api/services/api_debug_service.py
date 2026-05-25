"""Controlled API debug runner for the Vue API testing page."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
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
    params: dict[str, str] | None = None,
    body: str = "",
    body_type: str = "json",
    base_url: str = "",
    environment: dict[str, Any] | None = None,
    mock_config: dict[str, Any] | None = None,
    expected_status: int | None = None,
    json_assertions: list[dict[str, Any]] | None = None,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    """Run one controlled API debug request and evaluate basic assertions."""
    normalized_method = _validate_method(method)
    env = _normalize_environment(environment or {})
    env_variables = env["variables"]
    normalized_path = _validate_path(replace_variables(path, env_variables))
    normalized_headers = _replace_dict_values(
        {**env["headers"], **_normalize_headers(headers or {})},
        env_variables,
    )
    normalized_params = _replace_dict_values(params or {}, env_variables)
    effective_body = replace_variables(body, env_variables)
    effective_base_url = replace_variables(base_url.strip() or env["base_url"], env_variables)
    started = time.perf_counter()

    if mock_config and mock_config.get("enabled"):
        response = _send_configured_mock_response(mock_config)
        target_mode = "configured_mock"
    elif effective_base_url.strip():
        response = _send_local_http_request(
            method=normalized_method,
            base_url=effective_base_url,
            path=normalized_path,
            headers=normalized_headers,
            params=normalized_params,
            body=effective_body,
            timeout_seconds=timeout_seconds,
        )
        target_mode = "local_http_error" if response.get("transport_error") else "local_http"
    else:
        response = _send_mock_request(
            method=normalized_method,
            path=normalized_path,
            headers=normalized_headers,
            body=effective_body,
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
            "base_url": effective_base_url.strip(),
            "headers": normalized_headers,
            "params": normalized_params,
            "body": effective_body,
            "body_type": body_type,
            "environment": env,
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


def list_api_environments() -> list[dict[str, Any]]:
    """Return lightweight environment presets for the API workspace."""
    return [
        {
            "environment_id": "mock-local",
            "name": "内置 Mock 环境",
            "description": "默认环境，不请求真实服务，适合本地稳定演示。",
            "base_url": "",
            "variables": {
                "username": "tester",
                "password": "Passw0rd!",
                "wrong_password": "wrong",
                "filename": "demo.txt",
            },
            "headers": {"Content-Type": "application/json"},
        },
        {
            "environment_id": "local-api",
            "name": "本机 API 环境",
            "description": "只允许请求 localhost / 127.0.0.1，适合调试本机服务。",
            "base_url": "http://127.0.0.1:9000",
            "variables": {
                "username": "tester",
                "password": "Passw0rd!",
                "filename": "demo.txt",
            },
            "headers": {"Content-Type": "application/json"},
        },
    ]


def synthesize_api_test_cases(
    *,
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: str = "",
    count: int = 6,
) -> dict[str, Any]:
    """Generate deterministic API test mutations inspired by FullScopeTest."""
    normalized_method = _validate_method(method)
    normalized_path = _validate_path(path)
    base_payload = _parse_json_body(body)
    cases: list[dict[str, Any]] = []

    if normalized_path == "/api/login" and isinstance(base_payload, dict):
        cases.extend(
            [
                _case(
                    "正常登录",
                    normalized_method,
                    normalized_path,
                    headers,
                    {"username": "tester", "password": "Passw0rd!"},
                    200,
                    [{"path": "token", "operator": "exists"}],
                ),
                _case(
                    "错误密码",
                    normalized_method,
                    normalized_path,
                    headers,
                    {"username": "tester", "password": "wrong"},
                    401,
                    [{"path": "error", "operator": "equals", "expected": "invalid_credentials"}],
                ),
                _case(
                    "缺少密码字段",
                    normalized_method,
                    normalized_path,
                    headers,
                    {"username": "tester"},
                    400,
                    [{"path": "error", "operator": "equals", "expected": "missing_required_field"}],
                ),
                _case(
                    "空用户名",
                    normalized_method,
                    normalized_path,
                    headers,
                    {"username": "", "password": "Passw0rd!"},
                    400,
                    [{"path": "error", "operator": "exists"}],
                ),
                _case(
                    "SQL 注入密码",
                    normalized_method,
                    normalized_path,
                    headers,
                    {"username": "tester", "password": "' OR '1'='1"},
                    401,
                    [{"path": "error", "operator": "exists"}],
                ),
                _case(
                    "XSS 用户名",
                    normalized_method,
                    normalized_path,
                    headers,
                    {"username": "<script>alert(1)</script>", "password": "Passw0rd!"},
                    401,
                    [{"path": "error", "operator": "exists"}],
                ),
            ]
        )
    elif normalized_path == "/api/upload":
        cases.extend(
            [
                _case(
                    "文件上传成功",
                    normalized_method,
                    normalized_path,
                    {"Content-Type": "application/octet-stream", "X-Filename": "demo.txt"},
                    "demo-binary-content",
                    201,
                    [{"path": "filename", "operator": "equals", "expected": "demo.txt"}],
                ),
                _case(
                    "缺少文件名",
                    normalized_method,
                    normalized_path,
                    {"Content-Type": "application/octet-stream"},
                    "demo-binary-content",
                    400,
                    [{"path": "error", "operator": "equals", "expected": "missing_filename"}],
                ),
                _case(
                    "空文件内容",
                    normalized_method,
                    normalized_path,
                    {"Content-Type": "application/octet-stream", "X-Filename": "empty.txt"},
                    "",
                    201,
                    [{"path": "size", "operator": "equals", "expected": "0"}],
                ),
            ]
        )
    else:
        cases.extend(
            [
                _case("基础可用性检查", normalized_method, normalized_path, headers, base_payload, 200, []),
                _case("缺少鉴权头", normalized_method, normalized_path, {}, base_payload, 401, []),
                _case("异常输入探测", normalized_method, normalized_path, headers, {"payload": "' OR 1=1"}, 400, []),
            ]
        )

    selected = cases[: max(1, min(int(count or 6), 12))]
    return {
        "source": "deterministic_synthesizer",
        "base_request": {
            "method": normalized_method,
            "path": normalized_path,
            "headers": headers or {},
            "body": body,
        },
        "cases": selected,
        "summary": {
            "total": len(selected),
            "dimensions": ["happy_path", "negative", "boundary", "security"],
        },
    }


def generate_api_operation_plan(*, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a lightweight operation plan from natural language."""
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")

    lowered = text.lower()
    operations: list[dict[str, Any]] = []
    if any(token in lowered for token in ["环境", "environment", "base url", "base_url"]):
        operations.append(
            {
                "type": "create_environment",
                "name": "AI 生成环境",
                "base_url": "http://127.0.0.1:9000",
                "variables": {"username": "tester", "password": "Passw0rd!"},
                "headers": {"Content-Type": "application/json"},
            }
        )

    collection_name = "AI 生成接口集合"
    operations.append({"type": "create_collection", "name": collection_name})

    if any(token in lowered for token in ["上传", "upload", "文件"]):
        operations.append(
            {
                "type": "create_case",
                "name": "文件上传接口",
                "method": "POST",
                "path": "/api/upload",
                "headers": {"Content-Type": "application/octet-stream", "X-Filename": "{{filename}}"},
                "body": "demo-binary-content",
                "expected_status": 201,
            }
        )
    else:
        operations.append(
            {
                "type": "create_case",
                "name": "登录接口",
                "method": "POST",
                "path": "/api/login",
                "headers": {"Content-Type": "application/json"},
                "body": {"username": "{{username}}", "password": "{{password}}"},
                "expected_status": 200,
            }
        )

    if any(token in lowered for token in ["执行", "run", "测试", "execute"]):
        operations.append({"type": "run_collection", "collection_name": collection_name})

    return {
        "summary": "根据自然语言生成的接口测试操作计划",
        "source": "deterministic_planner",
        "context": context or {},
        "operations": operations,
    }


def export_curl_command(
    *,
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    body: str = "",
    base_url: str = "",
    environment: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Export a cURL command for the current API request."""
    env = _normalize_environment(environment or {})
    variables = env["variables"]
    effective_base_url = replace_variables(base_url.strip() or env["base_url"], variables)
    effective_path = _validate_path(replace_variables(path, variables))
    effective_headers = _replace_dict_values({**env["headers"], **(headers or {})}, variables)
    effective_params = _replace_dict_values(params or {}, variables)
    effective_body = replace_variables(body, variables)
    url = f"{effective_base_url.rstrip('/')}{effective_path}" if effective_base_url else effective_path
    if effective_params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(effective_params)}"
    parts = ["curl", "-X", _validate_method(method), _shell_quote(url)]
    for key, value in effective_headers.items():
        parts.extend(["-H", _shell_quote(f"{key}: {value}")])
    if effective_body:
        parts.extend(["--data", _shell_quote(effective_body)])
    return {"curl": " ".join(parts)}


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


def _send_configured_mock_response(mock_config: dict[str, Any]) -> dict[str, Any]:
    delay_ms = _to_int(mock_config.get("delay_ms"), default=0)
    if delay_ms > 0:
        time.sleep(min(delay_ms, 3000) / 1000)

    status_code = _to_int(mock_config.get("status_code"), default=200)
    headers = _normalize_headers(mock_config.get("headers") or {"Content-Type": "application/json"})
    body = mock_config.get("body", {})
    if isinstance(body, str):
        json_body = _try_json(body)
        raw_body = body
    else:
        json_body = body
        raw_body = json.dumps(body, ensure_ascii=False)
    return {
        "status_code": status_code,
        "headers": headers,
        "body": raw_body,
        "json": json_body,
    }


def _send_local_http_request(
    *,
    method: str,
    base_url: str,
    path: str,
    headers: dict[str, str],
    params: dict[str, str],
    body: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    parsed = urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("base_url must start with http:// or https://")
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("Only localhost targets are allowed for API debugging")

    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params)}"
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
        return _local_http_error_response(exc.reason, url)

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


def _normalize_environment(environment: dict[str, Any]) -> dict[str, Any]:
    return {
        "environment_id": str(environment.get("environment_id", "")),
        "name": str(environment.get("name", "")),
        "description": str(environment.get("description", "")),
        "base_url": str(environment.get("base_url", "") or ""),
        "variables": {
            str(key): str(value)
            for key, value in (environment.get("variables") or {}).items()
            if str(key)
        },
        "headers": _normalize_headers(environment.get("headers") or {}),
    }


def replace_variables(text: str, variables: dict[str, str]) -> str:
    """Replace Postman-style {{variable}} placeholders."""
    result = str(text or "")
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def _replace_dict_values(data: dict[str, Any], variables: dict[str, str]) -> dict[str, str]:
    return {str(key): replace_variables(str(value), variables) for key, value in data.items()}


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


def _local_http_error_response(reason: Any, url: str) -> dict[str, Any]:
    message = (
        "本机 HTTP 服务连接失败。通常是因为你选择了“本机 API 环境”，"
        "但没有在对应端口启动真实接口服务。演示时请切回“内置 Mock 环境”。"
    )
    payload = {
        "error": "local_http_connection_failed",
        "message": message,
        "reason": str(reason),
        "url": url,
    }
    return {
        "status_code": 0,
        "headers": {},
        "body": json.dumps(payload, ensure_ascii=False),
        "json": payload,
        "transport_error": True,
    }


def _case(
    name: str,
    method: str,
    path: str,
    headers: dict[str, str] | None,
    body: Any,
    expected_status: int,
    json_assertions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "name": name,
        "method": method,
        "path": path,
        "headers": headers or {},
        "body": json.dumps(body, ensure_ascii=False) if isinstance(body, (dict, list)) else str(body),
        "expected_status": expected_status,
        "json_assertions": json_assertions,
    }


def _to_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _shell_quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'

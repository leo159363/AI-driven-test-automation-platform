"""Demo automation scenario: API login."""

from __future__ import annotations

import json
from urllib import request
from urllib.error import HTTPError

import pytest


def _post_json(url: str, payload: dict[str, str]) -> tuple[int, dict[str, object]]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


@pytest.mark.automation
@pytest.mark.e2e
def test_api_login_success(demo_base_url: str) -> None:
    status, payload = _post_json(
        f"{demo_base_url}/api/login",
        {"username": "tester", "password": "Passw0rd!"},
    )

    assert status == 200
    assert payload["token"] == "demo-token"
    assert payload["user"] == "tester"


@pytest.mark.automation
@pytest.mark.e2e
def test_api_login_rejects_invalid_password(demo_base_url: str) -> None:
    status, payload = _post_json(
        f"{demo_base_url}/api/login",
        {"username": "tester", "password": "wrong-password"},
    )

    assert status == 401
    assert payload["error"] == "invalid_credentials"

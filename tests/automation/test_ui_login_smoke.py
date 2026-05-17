"""Demo automation scenario: UI login smoke."""

from __future__ import annotations

from urllib import parse, request
from urllib.error import HTTPError

import pytest


def _get_text(url: str) -> tuple[int, str]:
    with request.urlopen(url) as response:
        return response.status, response.read().decode("utf-8")


def _post_form(url: str, payload: dict[str, str]) -> tuple[int, str]:
    req = request.Request(
        url,
        data=parse.urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


@pytest.mark.automation
@pytest.mark.e2e
def test_ui_login_page_smoke(demo_base_url: str) -> None:
    status, html = _get_text(f"{demo_base_url}/login")

    assert status == 200
    assert "<title>Demo Login</title>" in html
    assert 'id="login-form"' in html
    assert 'name="username"' in html
    assert 'name="password"' in html


@pytest.mark.automation
@pytest.mark.e2e
def test_ui_login_form_submission_succeeds(demo_base_url: str) -> None:
    status, html = _post_form(
        f"{demo_base_url}/login",
        {"username": "tester", "password": "Passw0rd!"},
    )

    assert status == 200
    assert "Welcome Test User" in html

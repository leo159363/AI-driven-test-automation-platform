"""Demo automation scenario: API file upload."""

from __future__ import annotations

import json
from urllib import request
from urllib.error import HTTPError

import pytest


def _post_bytes(
    url: str,
    body: bytes,
    *,
    filename: str | None,
) -> tuple[int, dict[str, object]]:
    headers = {"Content-Type": "application/octet-stream"}
    if filename:
        headers["X-Filename"] = filename

    req = request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


@pytest.mark.automation
@pytest.mark.e2e
def test_api_file_upload_accepts_binary_payload(demo_base_url: str) -> None:
    status, payload = _post_bytes(
        f"{demo_base_url}/api/upload",
        b"demo-binary-content",
        filename="demo.txt",
    )

    assert status == 201
    assert payload["filename"] == "demo.txt"
    assert payload["size"] == len(b"demo-binary-content")


@pytest.mark.automation
@pytest.mark.e2e
def test_api_file_upload_requires_filename_header(demo_base_url: str) -> None:
    status, payload = _post_bytes(
        f"{demo_base_url}/api/upload",
        b"demo-binary-content",
        filename=None,
    )

    assert status == 400
    assert payload["error"] == "missing_filename"

"""Unit tests for the QualityPilot full-stack launcher helpers."""

from __future__ import annotations

from scripts import start_fullstack


def test_qualitypilot_health_payload_must_match_service_name() -> None:
    assert (
        start_fullstack._is_qualitypilot_health_payload(
            {"status": "ok", "service": "qualitypilot-api"}
        )
        is True
    )
    assert (
        start_fullstack._is_qualitypilot_health_payload(
            {"status": "ok", "service": "some-other-api"}
        )
        is False
    )
    assert start_fullstack._is_qualitypilot_health_payload({"detail": "Not Found"}) is False


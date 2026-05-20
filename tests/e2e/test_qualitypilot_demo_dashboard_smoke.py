"""Smoke test for the QualityPilot Demo dashboard page."""

from __future__ import annotations

from typing import Any

import pytest


def _collect_text(at: Any) -> str:
    parts: list[str] = []
    for attr in ("markdown", "header", "subheader", "info", "caption", "code"):
        for el in getattr(at, attr, []):
            parts.append(str(getattr(el, "value", "")))
    return "\n".join(parts)


@pytest.mark.e2e
def test_qualitypilot_demo_page_renders_without_running_demo() -> None:
    """The page should render even before demo artifacts exist."""
    from streamlit.testing.v1 import AppTest

    def page_script():
        from src.observability.dashboard.pages.qualitypilot_demo import render

        render()

    at = AppTest.from_function(page_script, default_timeout=10)
    at.run()

    assert not at.exception, f"QualityPilot Demo page raised an exception: {at.exception}"
    text = _collect_text(at)
    assert "qualitypilot" in text.lower()
    assert "workflow" in text.lower() or "demo" in text.lower()

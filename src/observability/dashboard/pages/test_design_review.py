"""Streamlit page for deterministic test-design review."""

from __future__ import annotations

import json

import streamlit as st

from src.observability.dashboard.services import (
    DEFAULT_EXPECTED_DIMENSIONS,
    DIMENSION_LABELS,
    review_test_design_markdown,
)


SAMPLE_MARKDOWN = """# Login API Test Design

## Functional
- Verify successful login returns HTTP 200, token, and user id.
- Verify invalid password returns HTTP 401 and error code INVALID_CREDENTIALS.

## Boundary
- Verify empty username, empty password, and overlong username are rejected with field errors.

## Exception
- Verify downstream timeout returns retryable error message and logs trace id.

## Security
- Verify expired token, replayed request, and unauthorized role are rejected.

## Regression
- Verify existing login clients remain compatible with the response schema.
"""


def render() -> None:
    """Render the test-design review page."""
    st.header("AI Test Design Review")
    st.markdown(
        "Review generated test-design Markdown for missing dimensions, vague cases, "
        "subjective assertions, and traceability gaps."
    )

    dimension_options = list(DIMENSION_LABELS.keys())
    expected_dimensions = st.multiselect(
        "Expected review dimensions",
        options=dimension_options,
        default=list(DEFAULT_EXPECTED_DIMENSIONS),
        format_func=lambda key: DIMENSION_LABELS[key],
        key="tdr_dimensions",
    )
    markdown = st.text_area(
        "Test-design Markdown",
        value=st.session_state.get("tw_draft", SAMPLE_MARKDOWN),
        height=360,
        key="tdr_markdown",
    )

    if st.button("Run Review", type="primary", key="tdr_run"):
        st.session_state["tdr_report"] = review_test_design_markdown(
            markdown,
            expected_dimensions=expected_dimensions,
        )

    report = st.session_state.get("tdr_report")
    if not report:
        st.info("Run the review to see score, risk level, missing dimensions, and findings.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", report.score)
    col2.metric("Risk", report.risk_level)
    col3.metric("Findings", len(report.findings))

    st.subheader("Dimension Coverage")
    covered_labels = [DIMENSION_LABELS.get(key, key) for key in report.covered_dimensions]
    missing_labels = [DIMENSION_LABELS.get(key, key) for key in report.missing_dimensions]
    st.write("Covered: " + (", ".join(covered_labels) if covered_labels else "None"))
    st.write("Missing: " + (", ".join(missing_labels) if missing_labels else "None"))

    st.subheader("Findings")
    if report.findings:
        st.dataframe(report.to_rows(), hide_index=True, use_container_width=True)
    else:
        st.success("No deterministic review findings.")

    st.subheader("JSON")
    st.code(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), language="json")

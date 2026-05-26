"""Tests for system platform capability configuration APIs."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.services.platform_config_service import reset_platform_configs_for_tests


@pytest.fixture(autouse=True)
def reset_platform_configs() -> None:
    reset_platform_configs_for_tests()


def _client() -> TestClient:
    return TestClient(create_app())


def test_get_platform_configs_returns_default_builtin_configs() -> None:
    response = _client().get("/api/settings/platform-configs")

    assert response.status_code == 200
    payload = response.json()
    keys = {item["key"] for item in payload["items"]}
    assert keys == {
        "rag_knowledge_store",
        "mcp_server",
        "test_runner",
        "allure_report",
        "agent_orchestration",
    }
    assert payload["summary"] == {"total": 5, "builtin": 5, "custom": 0}
    assert all(item["builtin"] is True for item in payload["items"])
    assert payload["items"][0]["value"]


def test_put_platform_config_updates_builtin_enabled_and_value() -> None:
    response = _client().put(
        "/api/settings/platform-configs/rag_knowledge_store",
        json={
            "name": "Ignored Name",
            "enabled": False,
            "value": {
                "enabled": False,
                "store": "local",
                "top_k": 8,
                "chunk_size": 600,
                "source_type_filter": ["requirement", "api_doc"],
            },
            "description": "ignored description",
        },
    )

    assert response.status_code == 200
    config = response.json()["config"]
    assert config["key"] == "rag_knowledge_store"
    assert config["name"] == "RAG Knowledge Store"
    assert config["enabled"] is False
    assert config["status"] == "disabled"
    assert config["value"]["top_k"] == 8
    assert "top_k=8" in config["summary"]


def test_post_platform_config_creates_custom_config() -> None:
    response = _client().post(
        "/api/settings/platform-configs",
        json={
            "key": "custom_report_path",
            "name": "Custom Report Path",
            "type": "custom",
            "enabled": True,
            "value": {
                "enabled": True,
                "report_dir": "artifacts/custom-report",
            },
            "description": "自定义报告目录。",
        },
    )

    assert response.status_code == 200
    config = response.json()["config"]
    assert config["key"] == "custom_report_path"
    assert config["builtin"] is False
    assert config["status"] == "enabled"

    list_response = _client().get("/api/settings/platform-configs")
    assert list_response.status_code == 200
    assert list_response.json()["summary"] == {"total": 6, "builtin": 5, "custom": 1}


def test_delete_platform_config_only_allows_custom_config() -> None:
    client = _client()
    create_response = client.post(
        "/api/settings/platform-configs",
        json={
            "key": "experimental_toggle",
            "name": "Experimental Toggle",
            "type": "custom",
            "enabled": False,
            "value": {"enabled": False, "feature": "demo"},
            "description": "实验开关。",
        },
    )
    assert create_response.status_code == 200

    delete_response = client.delete("/api/settings/platform-configs/experimental_toggle")
    assert delete_response.status_code == 200

    builtin_delete_response = client.delete("/api/settings/platform-configs/mcp_server")
    assert builtin_delete_response.status_code == 400
    assert "内置配置不允许删除" in builtin_delete_response.json()["detail"]


def test_platform_config_value_must_be_json_object() -> None:
    create_response = _client().post(
        "/api/settings/platform-configs",
        json={
            "key": "bad_config",
            "name": "Bad Config",
            "type": "custom",
            "enabled": True,
            "value": "not-json-object",
        },
    )

    assert create_response.status_code == 422

    update_response = _client().put(
        "/api/settings/platform-configs/test_runner",
        json={"value": "not-json-object"},
    )
    assert update_response.status_code == 422

"""Runtime model configuration for OpenAI-compatible providers."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

AI_MODEL_CONFIG: dict[str, Any] = {
    "enabled": False,
    "base_url": "",
    "model": "",
    "api_key": "",
    "vision_base_url": "",
    "vision_model": "",
    "vision_api_key": "",
    "updated_at": "",
}


def get_ai_model_config(*, mask_secrets: bool = True) -> dict[str, Any]:
    """Return the current model config, masking secrets by default."""
    config = dict(AI_MODEL_CONFIG)
    if mask_secrets:
        config["api_key"] = _mask_secret(str(config.get("api_key") or ""))
        config["vision_api_key"] = _mask_secret(str(config.get("vision_api_key") or ""))
    config["has_api_key"] = bool(AI_MODEL_CONFIG.get("api_key"))
    config["has_vision_api_key"] = bool(AI_MODEL_CONFIG.get("vision_api_key"))
    config["configured"] = _is_text_model_configured(AI_MODEL_CONFIG)
    config["vision_configured"] = _is_vision_model_configured(AI_MODEL_CONFIG)
    return config


def update_ai_model_config(payload: dict[str, Any], *, updated_at: str) -> dict[str, Any]:
    """Update the runtime model config.

    Empty API key fields preserve the existing keys, so the frontend can save non-secret fields
    without forcing users to re-enter keys every time.
    """
    AI_MODEL_CONFIG["enabled"] = bool(payload.get("enabled", False))
    AI_MODEL_CONFIG["base_url"] = str(payload.get("base_url") or "").strip().rstrip("/")
    AI_MODEL_CONFIG["model"] = str(payload.get("model") or "").strip()
    AI_MODEL_CONFIG["vision_base_url"] = str(payload.get("vision_base_url") or "").strip().rstrip("/")
    AI_MODEL_CONFIG["vision_model"] = str(payload.get("vision_model") or "").strip()
    if payload.get("api_key"):
        AI_MODEL_CONFIG["api_key"] = str(payload["api_key"]).strip()
    if payload.get("vision_api_key"):
        AI_MODEL_CONFIG["vision_api_key"] = str(payload["vision_api_key"]).strip()
    AI_MODEL_CONFIG["updated_at"] = updated_at
    return get_ai_model_config(mask_secrets=True)


def is_text_model_enabled() -> bool:
    """Return whether the real text model should be used."""
    return bool(AI_MODEL_CONFIG.get("enabled")) and _is_text_model_configured(AI_MODEL_CONFIG)


def current_model_metadata() -> dict[str, Any]:
    """Return non-secret metadata for assistant responses."""
    return {
        "enabled": bool(AI_MODEL_CONFIG.get("enabled")),
        "configured": _is_text_model_configured(AI_MODEL_CONFIG),
        "base_url": AI_MODEL_CONFIG.get("base_url") or "",
        "model": AI_MODEL_CONFIG.get("model") or "",
        "mode": "openai_compatible" if is_text_model_enabled() else "deterministic_demo",
    }


def generate_with_text_model(prompt: str, *, timeout_seconds: int = 30) -> dict[str, Any]:
    """Call the configured OpenAI-compatible chat completion endpoint."""
    if not is_text_model_enabled():
        return {
            "ok": False,
            "used_model": False,
            "message": "真实模型未启用或配置不完整，已使用本地确定性生成。",
        }
    try:
        payload = {
            "model": AI_MODEL_CONFIG["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是测试开发助手，请输出结构化、可执行、适合面试讲解的中文内容。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }
        data = _post_chat_completion(
            base_url=AI_MODEL_CONFIG["base_url"],
            api_key=AI_MODEL_CONFIG["api_key"],
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        content = _extract_chat_content(data)
        return {
            "ok": True,
            "used_model": True,
            "message": "真实模型调用成功。",
            "content": content,
            "model": AI_MODEL_CONFIG["model"],
            "base_url": AI_MODEL_CONFIG["base_url"],
        }
    except Exception as exc:  # pragma: no cover - depends on external provider/network
        return {
            "ok": False,
            "used_model": False,
            "message": f"真实模型调用失败，已回退本地确定性生成：{exc}",
            "model": AI_MODEL_CONFIG.get("model") or "",
            "base_url": AI_MODEL_CONFIG.get("base_url") or "",
        }


def test_text_model_connection(*, timeout_seconds: int = 10) -> dict[str, Any]:
    """Test the configured text model connection."""
    missing = _missing_text_model_fields(AI_MODEL_CONFIG)
    if missing:
        return {
            "ok": False,
            "configured": False,
            "message": f"文本模型配置不完整：{', '.join(missing)}",
            "model": AI_MODEL_CONFIG.get("model") or "",
            "base_url": AI_MODEL_CONFIG.get("base_url") or "",
        }
    result = _run_text_model_probe(timeout_seconds=timeout_seconds)
    return {
        "ok": bool(result.get("ok")),
        "configured": True,
        "message": result.get("message", ""),
        "model": AI_MODEL_CONFIG.get("model") or "",
        "base_url": AI_MODEL_CONFIG.get("base_url") or "",
        "sample": result.get("content", ""),
    }


def _run_text_model_probe(*, timeout_seconds: int) -> dict[str, Any]:
    """Call the configured text model once, regardless of the enabled switch."""
    try:
        payload = {
            "model": AI_MODEL_CONFIG["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个连通性测试探针，只需要简短回答。",
                },
                {"role": "user", "content": "请只回复 pong"},
            ],
            "temperature": 0,
            "max_tokens": 16,
        }
        data = _post_chat_completion(
            base_url=AI_MODEL_CONFIG["base_url"],
            api_key=AI_MODEL_CONFIG["api_key"],
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        return {
            "ok": True,
            "used_model": True,
            "message": "真实模型连接测试成功。",
            "content": _extract_chat_content(data),
        }
    except Exception as exc:  # pragma: no cover - depends on external provider/network
        return {
            "ok": False,
            "used_model": False,
            "message": f"真实模型连接测试失败：{exc}",
            "content": "",
        }


def _post_chat_completion(
    *,
    base_url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    url = _chat_completions_url(base_url)
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:300]}") from exc
    except URLError as exc:
        raise RuntimeError(f"无法连接模型服务：{exc.reason}") from exc


def _chat_completions_url(base_url: str) -> str:
    if base_url.rstrip("/").endswith("/chat/completions"):
        return base_url.rstrip("/")
    return f"{base_url.rstrip('/')}/chat/completions"


def _extract_chat_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return json.dumps(payload, ensure_ascii=False)
    first = choices[0]
    if not isinstance(first, dict):
        return json.dumps(payload, ensure_ascii=False)
    message = first.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    if isinstance(first.get("text"), str):
        return first["text"]
    return json.dumps(payload, ensure_ascii=False)


def _is_text_model_configured(config: dict[str, Any]) -> bool:
    return not _missing_text_model_fields(config)


def _is_vision_model_configured(config: dict[str, Any]) -> bool:
    return all(
        str(config.get(field) or "").strip()
        for field in ("vision_base_url", "vision_model", "vision_api_key")
    )


def _missing_text_model_fields(config: dict[str, Any]) -> list[str]:
    labels = {
        "base_url": "Base URL",
        "model": "模型名称",
        "api_key": "API Key",
    }
    return [label for field, label in labels.items() if not str(config.get(field) or "").strip()]


def _mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"

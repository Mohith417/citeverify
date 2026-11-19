"""Unified LLM client for structured JSON generation.

Providers
---------
* ``gemini``        – Google AI Studio free tier via the official ``google-genai`` SDK.
* ``groq``          – Groq free tier (OpenAI-compatible).
* ``openai_compat`` – any OpenAI-compatible endpoint free of charge.
* ``ollama``        – local models (OpenAI-compatible ``/v1`` endpoint).

The rest of the codebase only depends on :func:`generate_json`, so swapping the
provider never touches claim extraction or verification logic.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

GROQ_BASE = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class LLMError(Exception):
    pass


def _gemini_looks_valid(key: str) -> bool:
    # Google AI Studio keys start with "AIza"; other prefixes (e.g. "gsk") are
    # OpenAI-compatible provider keys and would fail against Gemini.
    return key.startswith("AIza")


def resolve() -> Optional[dict[str, str]]:
    """Return the active provider configuration, or ``None`` when unavailable."""
    provider = (settings.ai_provider or "auto").strip().lower()
    key = settings.ai_api_key or settings.gemini_api_key

    # A saved key may live in GEMINI_API_KEY even when the provider is not Gemini
    # (e.g. a Groq key). Detect the mismatch instead of failing silently.
    if provider == "gemini" and key and not _gemini_looks_valid(key):
        provider = "groq"

    if provider in ("auto", ""):
        if settings.gemini_api_key and _gemini_looks_valid(settings.gemini_api_key) and settings.gemini_model:
            provider = "gemini"
        elif key.startswith("gsk_"):
            provider = "groq"
        elif settings.ai_base_url:
            provider = "openai_compat"
        elif settings.ollama_model:
            provider = "ollama"
        else:
            return None

    if provider == "gemini":
        gemini_key = settings.gemini_api_key or settings.ai_api_key
        if not gemini_key or not settings.gemini_model:
            return None
        return {"provider": "gemini", "model": settings.gemini_model, "key": gemini_key}

    if provider == "groq":
        if not key:
            return None
        return {
            "provider": "groq",
            "model": settings.ai_model or DEFAULT_GROQ_MODEL,
            "base_url": settings.ai_base_url or GROQ_BASE,
            "key": key,
        }

    if provider == "ollama":
        if not settings.ollama_model:
            return None
        return {
            "provider": "ollama",
            "model": settings.ollama_model,
            "base_url": (settings.ai_base_url or f"{settings.ollama_url.rstrip('/')}/v1"),
            "key": "ollama",
        }

    if provider in ("openai_compat", "openai"):
        if not settings.ai_base_url:
            return None
        return {
            "provider": "openai_compat",
            "model": settings.ai_model,
            "base_url": settings.ai_base_url,
            "key": key,
        }

    return None


def is_available() -> bool:
    return resolve() is not None


def provider_label() -> str:
    cfg = resolve()
    if cfg is None:
        return "not configured"
    return f"{cfg['provider']}:{cfg['model']}"


def _extract_json(raw: str) -> dict[str, Any]:
    """Parse JSON from a model reply, tolerating fences or surrounding prose."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model returned invalid JSON: {exc}") from exc
    raise LLMError("Model returned no JSON object.")


def _gemini_json(system: str, prompt: str, model: str, key: str, response_schema) -> dict[str, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:  # pragma: no cover
        raise LLMError("google-genai is not installed.") from exc

    client = genai.Client(api_key=key)
    config_kwargs: dict[str, Any] = {
        "temperature": 0.1,
        "response_mime_type": "application/json",
        "system_instruction": system,
    }
    if response_schema is not None:
        config_kwargs["response_schema"] = response_schema
    response = client.models.generate_content(
        model=model, contents=prompt, config=types.GenerateContentConfig(**config_kwargs)
    )
    return _extract_json(response.text or "")


def _openai_json(system: str, prompt: str, cfg: dict[str, str]) -> dict[str, Any]:
    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"
    body = {
        "model": cfg["model"],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    last_error = ""
    # The provider may reject json_object mode for some models; retry plain.
    for attempt in range(2):
        try:
            r = httpx.post(url, json=body, headers=headers, timeout=120)
        except httpx.HTTPError as exc:
            raise LLMError(f"AI provider unreachable: {exc}") from exc
        if r.status_code == 429:
            raise LLMError("AI provider rate limit reached (HTTP 429). Try again shortly.")
        if r.status_code >= 400:
            last_error = f"HTTP {r.status_code}: {r.text[:300]}"
            if attempt == 0 and "response_format" in r.text:
                body.pop("response_format", None)
                continue
            raise LLMError(f"AI provider error — {last_error}")
        data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError("AI provider returned an unexpected response.") from exc
        return _extract_json(content or "")
    raise LLMError(f"AI provider error — {last_error}")


def generate_json(
    *,
    system: str,
    prompt: str,
    response_schema=None,
) -> dict[str, Any]:
    """Ask the configured model for a JSON object and parse it."""
    cfg = resolve()
    if cfg is None:
        raise LLMError(
            "No AI provider configured. Set GEMINI_API_KEY + GEMINI_MODEL, "
            "or AI_PROVIDER/AI_MODEL/AI_BASE_URL/AI_API_KEY for an OpenAI-compatible endpoint."
        )
    if cfg["provider"] == "gemini":
        return _gemini_json(system, prompt, cfg["model"], cfg["key"], response_schema)
    return _openai_json(system, prompt, cfg)

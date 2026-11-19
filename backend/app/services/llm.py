
"""Unified LLM client with automatic provider fallback.

Primary: Gemini
Secondary: Groq

The public generate_json() interface remains compatible with existing services.
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
GROQ_MAX_COMPLETION_TOKENS = 4096


class LLMError(Exception):
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


def _gemini_looks_valid(key: str) -> bool:
    return bool(key and key.startswith("AIza"))


def _gemini_config() -> Optional[dict[str, str]]:
    key = settings.gemini_api_key
    if not key or not settings.gemini_model:
        return None
    return {
        "provider": "gemini",
        "model": settings.gemini_model,
        "key": key,
    }


def _groq_config() -> Optional[dict[str, str]]:
    key = settings.ai_api_key
    if not key:
        return None
    return {
        "provider": "groq",
        "model": settings.ai_model or DEFAULT_GROQ_MODEL,
        "base_url": settings.ai_base_url or GROQ_BASE,
        "key": key,
    }


def _provider_configs() -> list[dict[str, str]]:
    """Return configured providers in priority order."""
    provider = (settings.ai_provider or "auto").strip().lower()

    gemini = _gemini_config()
    groq = _groq_config()

    if provider in ("auto", "gemini", ""):
        ordered = [gemini, groq]
    elif provider == "groq":
        ordered = [groq, gemini]
    elif provider == "ollama" and settings.ollama_model:
        ordered = [{
            "provider": "ollama",
            "model": settings.ollama_model,
            "base_url": (
                settings.ai_base_url
                or f"{settings.ollama_url.rstrip('/')}/v1"
            ),
            "key": "ollama",
        }]
    elif provider in ("openai_compat", "openai") and settings.ai_base_url:
        ordered = [{
            "provider": "openai_compat",
            "model": settings.ai_model,
            "base_url": settings.ai_base_url,
            "key": settings.ai_api_key,
        }]
    else:
        ordered = []

    return [cfg for cfg in ordered if cfg is not None]


def resolve() -> Optional[dict[str, str]]:
    """Return the primary configured provider."""
    providers = _provider_configs()
    return providers[0] if providers else None


def is_available() -> bool:
    return bool(_provider_configs())


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
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        raise LLMError("Model returned JSON, but it was not an object.", True)
    except json.JSONDecodeError:
        pass

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            result = json.loads(text[start:end + 1])
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    raise LLMError("Model returned invalid or missing JSON.", True)


def _gemini_json(
    system: str,
    prompt: str,
    model: str,
    key: str,
    response_schema=None,
) -> dict[str, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise LLMError("google-genai is not installed.") from exc

    try:
        client = genai.Client(api_key=key)

        config_kwargs: dict[str, Any] = {
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "system_instruction": system,
        }

        if response_schema is not None:
            config_kwargs["response_schema"] = response_schema

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        return _extract_json(response.text or "")

    except LLMError:
        raise
    except Exception as exc:
        status = (
            getattr(exc, "code", None)
            or getattr(exc, "status_code", None)
        )
        retryable = (
            status == 429
            or (isinstance(status, int) and status >= 500)
            or isinstance(exc, (TimeoutError, ConnectionError, httpx.HTTPError))
        )
        raise LLMError(
            f"Gemini request failed ({status or type(exc).__name__}): {exc}",
            retryable=retryable,
        ) from exc


def _openai_json(
    system: str,
    prompt: str,
    cfg: dict[str, str],
) -> dict[str, Any]:
    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"

    body = {
        "model": cfg["model"],
        "temperature": 0.1,
        "max_completion_tokens": GROQ_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            url,
            json=body,
            headers=headers,
            timeout=httpx.Timeout(90.0, connect=10.0),
        )
    except httpx.HTTPError as exc:
        raise LLMError(
            f"{cfg['provider']} network error: {exc}",
            retryable=True,
        ) from exc

    if response.status_code >= 400:
        # Retry once without JSON response_format if the endpoint
        # specifically rejects that parameter.
        if (
            response.status_code == 400
            and "response_format" in response.text.lower()
        ):
            body.pop("response_format", None)
            try:
                response = httpx.post(
                    url,
                    json=body,
                    headers=headers,
                    timeout=httpx.Timeout(90.0, connect=10.0),
                )
            except httpx.HTTPError as exc:
                raise LLMError(
                    f"{cfg['provider']} network error: {exc}",
                    retryable=True,
                ) from exc

        if response.status_code >= 400:
            status = response.status_code
            raise LLMError(
                f"{cfg['provider']} returned HTTP {status}: "
                f"{response.text[:300]}",
                retryable=(status == 429 or status >= 500),
            )

    try:
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""

        if not content.strip():
            finish = choice.get("finish_reason", "unknown")
            raise LLMError(
                f"{cfg['provider']} returned empty content "
                f"(finish reason: {finish}).",
                retryable=True,
            )

        return _extract_json(content)

    except LLMError:
        raise
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError(
            f"{cfg['provider']} returned an unexpected response: {exc}",
            retryable=True,
        ) from exc


def _call_provider(
    cfg: dict[str, str],
    system: str,
    prompt: str,
    response_schema=None,
) -> dict[str, Any]:
    if cfg["provider"] == "gemini":
        return _gemini_json(
            system,
            prompt,
            cfg["model"],
            cfg["key"],
            response_schema,
        )

    return _openai_json(system, prompt, cfg)


def generate_json(
    *,
    system: str,
    prompt: str,
    response_schema=None,
) -> dict[str, Any]:
    """Generate JSON using the primary provider and configured fallbacks."""
    providers = _provider_configs()

    if not providers:
        raise LLMError(
            "No AI provider configured. Set GEMINI_API_KEY and GEMINI_MODEL, "
            "or configure AI_API_KEY and AI_MODEL for Groq."
        )

    errors = []

    for index, cfg in enumerate(providers):
        name = cfg["provider"]

        try:
            result = _call_provider(
                cfg,
                system,
                prompt,
                response_schema,
            )
            logger.info(
                "LLM request completed successfully using %s:%s",
                name,
                cfg["model"],
            )
            return result

        except LLMError as exc:
            errors.append(f"{name}: {exc}")

            has_fallback = index < len(providers) - 1

            if not has_fallback or not exc.retryable:
                logger.error("LLM provider %s failed: %s", name, exc)
                break

            logger.warning(
                "LLM provider %s failed; switching to %s. Reason: %s",
                name,
                providers[index + 1]["provider"],
                exc,
            )

    raise LLMError(
        "All available AI providers failed. " + " | ".join(errors)
    )

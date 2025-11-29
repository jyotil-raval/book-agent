"""
LLM provider adapters for backend.
Supports OpenAI by default. Uses centralized secret loader to fetch API keys securely.

Behavior:
- If OpenAI responds 429 (insufficient_quota / rate limit), this module will
  optionally retry once with a fallback model (OPENAI_FALLBACK_MODEL env var).
- If no fallback or retry fails, a clear RuntimeError is raised to be returned
  to the GraphQL client.
"""
import os
import time
import httpx
import json
from typing import Optional

from ..secrets import get_secret

OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL")  # e.g. "gpt-3.5-turbo"

async def generate_text(prompt: str, provider: str = "openai", model: Optional[str] = None) -> str:
    provider = (provider or "openai").lower()
    if provider == "openai":
        openai_key = get_secret("OPENAI_KEY", required=True)
        return await _call_openai(prompt, openai_key, model or OPENAI_DEFAULT_MODEL)
    elif provider == "gemini":
        raise NotImplementedError("Gemini provider not implemented yet.")
    elif provider == "perplexity":
        raise NotImplementedError("Perplexity provider not implemented yet.")
    else:
        raise ValueError(f"Unknown provider '{provider}'")


async def _call_openai(prompt: str, openai_key: str, model: str = OPENAI_DEFAULT_MODEL,
                       max_tokens: int = 700, temperature: float = 0.6) -> str:
    if not openai_key:
        raise RuntimeError("OpenAI key missing")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    # Small retry/backoff for transient 429s; optionally retry once with fallback model.
    backoff_seconds = 1.0
    max_attempts = 2  # initial attempt + one retry (either backoff or fallback)
    attempt = 0
    last_exception = None

    async with httpx.AsyncClient(timeout=120) as client:
        while attempt < max_attempts:
            attempt += 1
            try:
                r = await client.post(url, json=payload, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    try:
                        return data["choices"][0]["message"]["content"]
                    except Exception:
                        return data.get("choices", [{}])[0].get("text") or json.dumps(data)
                # Handle 429 specifically
                if r.status_code == 429:
                    body = r.text
                    # if fallback model configured and we haven't retried with it yet, switch
                    if OPENAI_FALLBACK_MODEL and attempt == 1:
                        # attempt fallback model once
                        payload["model"] = OPENAI_FALLBACK_MODEL
                        # small backoff before retrying
                        time.sleep(backoff_seconds)
                        backoff_seconds *= 2
                        continue
                    # Otherwise raise a friendly error
                    short = body[:400] + ("..." if len(body) > 400 else "")
                    raise RuntimeError(
                        "OpenAI returned 429 (quota or rate limit). "
                        "Check your OpenAI billing/usage dashboard or set a fallback model. "
                        f"OpenAI message: {short}"
                    )
                # Other 4xx/5xx: raise with trimmed body (no secrets)
                if r.status_code >= 400:
                    text = r.text
                    short = text[:400] + ("..." if len(text) > 400 else "")
                    raise RuntimeError(f"OpenAI API error: {r.status_code} {short}")

            except httpx.RequestError as e:
                # network error - maybe transient; backoff and retry once
                last_exception = e
                if attempt < max_attempts:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                raise RuntimeError(f"Network error when contacting OpenAI: {e}") from e

    # If we exit loop without return
    raise RuntimeError("OpenAI request failed.") from last_exception
import os
import httpx
import json

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

async def call_openai(prompt: str, model: str = OPENAI_DEFAULT_MODEL) -> str:
    if not OPENAI_KEY:
        raise RuntimeError("OpenAI API key not configured (OPENAI_KEY)")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.6
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return data.get("choices", [{}])[0].get("text") or json.dumps(data)

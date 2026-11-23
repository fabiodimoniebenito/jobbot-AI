import json
import re

import requests

from jobbot.config import LLM_PROVIDER, MODEL, OLLAMA_NUM_CTX, OLLAMA_URL


def _llm_text(system: str, user: str, max_tokens: int, model: str) -> str:
    if LLM_PROVIDER == "ollama":
        r = requests.post(f"{OLLAMA_URL}/api/chat", timeout=600, json={
            "model": model, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"num_ctx": OLLAMA_NUM_CTX, "num_predict": max_tokens, "temperature": 0.3},
        })
        r.raise_for_status()
        d = r.json()
        if d.get("done_reason") == "length":
            raise ValueError(f"respuesta cortada por num_predict ({max_tokens}); sube el límite")
        return d["message"]["content"]

    from anthropic import Anthropic

    client = Anthropic()  # usa ANTHROPIC_API_KEY
    r = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if r.stop_reason == "max_tokens":
        raise ValueError(f"respuesta cortada por max_tokens ({max_tokens}); sube el límite")
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


def claude_json(system: str, user: str, max_tokens: int = 2000, model: str | None = None) -> dict:
    # los modelos locales fallan más el JSON: un reintento
    for intento in range(2 if LLM_PROVIDER == "ollama" else 1):
        txt = _llm_text(system, user, max_tokens, model or MODEL)
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            if m:
                return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError("el modelo no devolvió JSON válido")

"""Stage 10 – Global search helpers + offline-first status."""

from __future__ import annotations

from typing import Any


def offline_status(
    *,
    ollama_reachable: bool | None = None,
    libretranslate_reachable: bool | None = None,
    cloud_openai_reachable: bool | None = None,
) -> dict[str, Any]:
    local_ok = bool(ollama_reachable)
    message = None
    mode = 'online'
    if cloud_openai_reachable is False and local_ok:
        mode = 'offline_local'
        message = 'Cloud provider unavailable; local model is available.'
    elif cloud_openai_reachable is False and not local_ok:
        mode = 'degraded'
        message = 'Cloud provider unavailable; no local model detected.'
    elif ollama_reachable is False and cloud_openai_reachable is not False:
        mode = 'online'
        message = 'Local Ollama not reachable; cloud providers may still work.'

    return {
        'mode': mode,
        'message': message,
        'providers': {
            'ollama_local': ollama_reachable,
            'libretranslate_local': libretranslate_reachable,
            'cloud_openai': cloud_openai_reachable,
        },
        'prefer_local_when_cloud_down': True,
        'local_capabilities': [
            'Ollama local models',
            'LibreTranslate (if configured)',
            'local files',
            'local 3D preview',
        ],
    }


def search_rank(query: str, text: str) -> float:
    if not query or not text:
        return 0.0
    q = query.lower().strip()
    t = text.lower()
    if q in t:
        pos = t.find(q)
        return 100.0 - min(pos, 50) + min(t.count(q), 5)
    tokens = [w for w in q.split() if len(w) > 1]
    if not tokens:
        return 0.0
    hits = sum(1 for w in tokens if w in t)
    return (hits / len(tokens)) * 40.0

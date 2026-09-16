"""Stage 6 – Model Intelligence helpers.

Smart routing, fallback policy, duplicate detection, and health scoring.
Designed to sit on top of existing Ollama / OpenAI connection data without
rewriting upstream model loading.
"""

from __future__ import annotations

import re
import time
from typing import Any

TASK_KEYWORDS: dict[str, tuple[str, ...]] = {
    'coding': ('code', 'python', 'javascript', 'typescript', 'debug', 'refactor', 'compile'),
    'reasoning': ('reason', 'think', 'logic', 'math', 'proof', 'plan'),
    'translation': ('translate', 'hebrew', 'english', 'locale', 'i18n'),
    'vision': ('vision', 'image', 'screenshot', 'photo', 'ocr', 'llava', 'minicpm-v'),
    'simple': ('hello', 'hi', 'thanks', 'ok', 'yes', 'no'),
    'long_context': ('long context', 'document', 'summarize book', 'large file', '32k', '128k'),
    'local_private': ('private', 'local only', 'offline', 'airgap'),
}

CAPABILITY_HINTS: dict[str, tuple[str, ...]] = {
    'coding': ('code', 'coder', 'deepseek-coder', 'qwen2.5-coder', 'starcoder', 'codellama'),
    'reasoning': ('r1', 'reason', 'qwq', 'think', 'o1'),
    'translation': ('translate', 'nllb', 'madlad'),
    'vision': ('llava', 'vision', 'minicpm-v', 'moondream', 'bakllava'),
    'long_context': ('32k', '64k', '128k', 'longcontext', 'yarn'),
}


def classify_task(prompt: str | None, explicit: str | None = None) -> str:
    if explicit and explicit in TASK_KEYWORDS:
        return explicit
    text = (prompt or '').casefold()
    scores: dict[str, int] = {}
    for task, keywords in TASK_KEYWORDS.items():
        scores[task] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'simple'


def _name_blob(model: dict[str, Any]) -> str:
    parts = [
        str(model.get('id') or ''),
        str(model.get('name') or ''),
        str(model.get('model') or ''),
        str((model.get('meta') or {}).get('description') or '') if isinstance(model.get('meta'), dict) else '',
    ]
    return ' '.join(parts).casefold()


def score_model_for_task(model: dict[str, Any], task: str, prefer_local: bool = True) -> float:
    blob = _name_blob(model)
    score = 0.0
    for hint in CAPABILITY_HINTS.get(task, ()):
        if hint in blob:
            score += 3.0
    if task == 'local_private' and str(model.get('owned_by') or model.get('connection_type') or '').lower() in {
        'ollama',
        'local',
    }:
        score += 5.0
    if prefer_local and ('ollama' in blob or model.get('owned_by') == 'ollama'):
        score += 1.5
    if model.get('available', True) is False:
        score -= 100.0
    size = model.get('size') or model.get('parameter_size')
    if task == 'simple' and size:
        try:
            digits = re.findall(r'[\d.]+', str(size))
            if digits and float(digits[0]) <= 8:
                score += 1.0
        except Exception:
            pass
    return score


def route_models(
    models: list[dict[str, Any]],
    prompt: str | None = None,
    task: str | None = None,
    prefer_local: bool = True,
    limit: int = 5,
) -> dict[str, Any]:
    chosen_task = classify_task(prompt, task)
    ranked = sorted(
        (
            {
                **model,
                'route_score': score_model_for_task(model, chosen_task, prefer_local=prefer_local),
            }
            for model in models
        ),
        key=lambda item: item['route_score'],
        reverse=True,
    )
    return {
        'task': chosen_task,
        'recommendations': ranked[: max(1, limit)],
        'policy': {'prefer_local': prefer_local, 'limit': limit},
    }


def build_fallback_chain(
    models: list[dict[str, Any]],
    primary_id: str,
    task: str | None = None,
    max_fallbacks: int = 3,
) -> list[str]:
    routed = route_models(models, task=task or 'simple', limit=20)
    chain: list[str] = []
    for item in routed['recommendations']:
        mid = str(item.get('id') or item.get('name') or '')
        if not mid or mid == primary_id or mid in chain:
            continue
        chain.append(mid)
        if len(chain) >= max_fallbacks:
            break
    return chain


def detect_duplicate_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for model in models:
        mid = str(model.get('id') or model.get('name') or '')
        if not mid:
            continue
        base = mid.split(':')[0].split('/')[-1].casefold()
        base = re.sub(r'[-_](latest|instruct|chat)$', '', base)
        groups.setdefault(base, []).append(mid)
    findings = []
    for base, ids in groups.items():
        unique = list(dict.fromkeys(ids))
        if len(unique) > 1:
            findings.append(
                {
                    'normalized': base,
                    'entries': unique,
                    'message': f'Seeming duplicate model entries for "{base}"',
                    'action': 'diagnostic_only',
                }
            )
    return findings


def health_status_from_checks(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return 'misconfigured'
    if any(c.get('status') == 'offline' for c in checks):
        if all(c.get('status') == 'offline' for c in checks):
            return 'offline'
        return 'degraded'
    if any(c.get('status') in {'degraded', 'misconfigured'} for c in checks):
        return 'degraded'
    return 'healthy'


def warmup_plan(model_ids: list[str], max_warm: int = 3) -> dict[str, Any]:
    unique = list(dict.fromkeys(mid for mid in model_ids if mid))
    selected = unique[: max(1, max_warm)]
    return {
        'requested': unique,
        'selected': selected,
        'deferred': unique[len(selected) :],
        'limit': max_warm,
        'generated_at': int(time.time()),
    }

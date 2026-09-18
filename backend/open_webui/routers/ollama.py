"""Ollama router with keep_alive normalization (fixes missing unit in duration \"-1\")."""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

from fastapi import Depends, Request
from open_webui.models.config import Config
from open_webui.routers import ollama_legacy as _legacy
from open_webui.utils.auth import get_admin_user
from open_webui.utils.json_codec import JSONCodec
from pydantic import BaseModel, Field

router = _legacy.router

_PERF_KEYS = {
    'keep_alive': 'ollama.performance.keep_alive',
    'flash_attention': 'ollama.performance.flash_attention',
    'num_parallel': 'ollama.performance.num_parallel',
}
_NATIVE_KEEP_ALIVE_ENDPOINTS = ('/api/chat', '/api/generate', '/api/embed', '/api/embeddings')
_original_send_request = _legacy.send_request


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


def _normalize_keep_alive(value: Any) -> Any:
    """String \"-1\" breaks Go duration parsing; send int -1 for forever."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    if s == '':
        return '5m'
    if s in {'-1', '-1.0'} or (s.startswith('-') and s[1:].isdigit() and '.' not in s):
        return int(s)
    if s in {'0', '0.0'}:
        return 0
    return s


async def _performance_values() -> dict[str, Any]:
    values = await Config.get_many(*_PERF_KEYS.values())
    keep_alive = values.get(_PERF_KEYS['keep_alive'])
    flash_attention = values.get(_PERF_KEYS['flash_attention'])
    num_parallel = values.get(_PERF_KEYS['num_parallel'])
    raw = keep_alive if keep_alive is not None else os.getenv('OLLAMA_KEEP_ALIVE', '-1')
    return {
        'OLLAMA_KEEP_ALIVE': _normalize_keep_alive(raw),
        'OLLAMA_FLASH_ATTENTION': (
            flash_attention if flash_attention is not None else _env_bool('OLLAMA_FLASH_ATTENTION', True)
        ),
        'OLLAMA_NUM_PARALLEL': int(num_parallel if num_parallel is not None else os.getenv('OLLAMA_NUM_PARALLEL', '2')),
    }


async def send_request(url: str, method: str = 'POST', *, payload=None, **kwargs):
    if method.upper() == 'POST' and payload is not None and url.endswith(_NATIVE_KEEP_ALIVE_ENDPOINTS):
        try:
            was_bytes = isinstance(payload, (bytes, bytearray))
            raw = payload.decode('utf-8') if was_bytes else payload
            body = JSONCodec.loads(raw) if isinstance(raw, str) else raw
            if isinstance(body, dict):
                if body.get('keep_alive') is None:
                    body['keep_alive'] = (await _performance_values())['OLLAMA_KEEP_ALIVE']
                else:
                    body['keep_alive'] = _normalize_keep_alive(body.get('keep_alive'))
                encoded = JSONCodec.dumps(body)
                payload = encoded.encode('utf-8') if was_bytes else encoded
        except Exception as exc:
            _legacy.log.warning('Unable to apply Ollama keep_alive default: %s', exc)
    return await _original_send_request(url, method, payload=payload, **kwargs)


class PerformanceConfigForm(BaseModel):
    OLLAMA_KEEP_ALIVE: str = '-1'
    OLLAMA_FLASH_ATTENTION: bool = True
    OLLAMA_NUM_PARALLEL: int = Field(default=2, ge=1, le=16)


@router.get('/performance')
async def get_performance_config(user=Depends(get_admin_user)) -> dict:
    values = await _performance_values()
    ka = values['OLLAMA_KEEP_ALIVE']
    return {
        **values,
        'OLLAMA_KEEP_ALIVE': str(ka),
        'KEEP_MODELS_LOADED': (ka == -1) or str(ka).strip().startswith('-'),
    }


@router.post('/performance')
async def set_performance_config(form_data: PerformanceConfigForm, user=Depends(get_admin_user)) -> dict:
    keep_alive = form_data.OLLAMA_KEEP_ALIVE.strip() or '5m'
    if keep_alive in {'-1', '-1.0'}:
        keep_alive = '-1'
    await Config.upsert(
        {
            _PERF_KEYS['keep_alive']: keep_alive,
            _PERF_KEYS['flash_attention']: form_data.OLLAMA_FLASH_ATTENTION,
            _PERF_KEYS['num_parallel']: form_data.OLLAMA_NUM_PARALLEL,
        }
    )
    return await get_performance_config(user)


def _expiry_is_effectively_forever(expires_at: Any) -> bool:
    if not expires_at:
        return False
    try:
        parsed = dt.datetime.fromisoformat(str(expires_at).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)
        return parsed > dt.datetime.now(dt.UTC) + dt.timedelta(days=3650)
    except (TypeError, ValueError):
        return str(expires_at).lower() in {'forever', 'infinite', 'infinity'}


@router.get('/performance/diagnostics')
async def get_performance_diagnostics(request: Request, user=Depends(get_admin_user)) -> dict:
    performance = await _performance_values()
    loaded = await _legacy.get_ollama_loaded_models(request, user=user)
    models = []
    for model in loaded.get('models', []):
        expires_at = model.get('expires_at')
        forever = _expiry_is_effectively_forever(expires_at)
        models.append({**model, 'until': 'Forever' if forever else expires_at, 'keep_alive_forever': forever})
    ka = performance['OLLAMA_KEEP_ALIVE']
    configured_forever = (ka == -1) or str(ka).strip().startswith('-')
    finite_models = [model['model'] for model in models if not model['keep_alive_forever']]
    return {
        'models': models,
        'configured_keep_alive': ka,
        'configured_forever': configured_forever,
        'finite_models': finite_models,
        'warning': (
            'One or more loaded models have a finite expiry.'
            if configured_forever and finite_models
            else None
        ),
    }


def __getattr__(name: str):
    return getattr(_legacy, name)

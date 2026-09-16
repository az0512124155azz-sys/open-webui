"""Stage 6 – Model Intelligence API.

Smart router, fallback chains, health center, warmup plan, update check,
and duplicate detector. All mutating actions require explicit user intent.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.model_intelligence import (
    build_fallback_chain,
    detect_duplicate_models,
    health_status_from_checks,
    route_models,
    warmup_plan,
)
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter()


class RouteRequest(BaseModel):
    prompt: Optional[str] = None
    task: Optional[str] = None
    prefer_local: bool = True
    limit: int = 5
    models: list[dict[str, Any]] = Field(default_factory=list)


class FallbackRequest(BaseModel):
    primary_id: str
    task: Optional[str] = None
    max_fallbacks: int = 3
    models: list[dict[str, Any]] = Field(default_factory=list)


class WarmupRequest(BaseModel):
    model_ids: list[str] = Field(default_factory=list)
    max_warm: int = 3
    execute: bool = False


class BenchmarkRequest(BaseModel):
    model: str
    prompt: str = 'Say hello in one short sentence.'
    max_tokens: int = 32


async def _ollama_base() -> str:
    return os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434').split(';')[0].rstrip('/')


async def _fetch_ollama_tags() -> list[dict[str, Any]]:
    base = await _ollama_base()
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        async with session.get(f'{base}/api/tags') as response:
            response.raise_for_status()
            data = await response.json()
    models = []
    for item in data.get('models') or []:
        models.append(
            {
                'id': item.get('name') or item.get('model'),
                'name': item.get('name') or item.get('model'),
                'size': item.get('size'),
                'digest': item.get('digest'),
                'owned_by': 'ollama',
                'available': True,
                'modified_at': item.get('modified_at'),
            }
        )
    return models


@router.post('/route')
async def smart_route(form_data: RouteRequest, user=Depends(get_verified_user)):
    models = form_data.models
    if not models:
        try:
            models = await _fetch_ollama_tags()
        except Exception as exc:
            log.warning('route: failed to list ollama models: %s', exc)
            models = []
    return route_models(
        models,
        prompt=form_data.prompt,
        task=form_data.task,
        prefer_local=form_data.prefer_local,
        limit=form_data.limit,
    )


@router.post('/fallback')
async def fallback_chain(form_data: FallbackRequest, user=Depends(get_verified_user)):
    models = form_data.models
    if not models:
        try:
            models = await _fetch_ollama_tags()
        except Exception:
            models = []
    chain = build_fallback_chain(
        models,
        primary_id=form_data.primary_id,
        task=form_data.task,
        max_fallbacks=form_data.max_fallbacks,
    )
    return {
        'primary_id': form_data.primary_id,
        'fallbacks': chain,
        'notes': 'Policy only — caller must apply one hop at a time and never loop.',
    }


@router.get('/duplicates')
async def duplicate_detector(user=Depends(get_verified_user)):
    try:
        models = await _fetch_ollama_tags()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    findings = detect_duplicate_models(models)
    return {'findings': findings, 'count': len(findings), 'action': 'diagnostic_only'}


@router.get('/health')
async def connection_health_center(user=Depends(get_verified_user)):
    checks: list[dict[str, Any]] = []
    ollama_base = await _ollama_base()
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            t0 = time.perf_counter()
            async with session.get(f'{ollama_base}/api/ps') as response:
                ok = response.status < 400
                body = await response.json(content_type=None) if ok else {}
            latency_ms = int((time.perf_counter() - t0) * 1000)
        checks.append(
            {
                'id': 'ollama',
                'label': 'Ollama',
                'status': 'healthy' if ok else 'degraded',
                'latency_ms': latency_ms,
                'detail': f"{len((body or {}).get('models') or [])} loaded models",
            }
        )
    except Exception as exc:
        checks.append({'id': 'ollama', 'label': 'Ollama', 'status': 'offline', 'detail': str(exc)})

    lt = os.getenv('LIBRETRANSLATE_BASE_URL', 'http://libretranslate:5000').rstrip('/')
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            t0 = time.perf_counter()
            async with session.get(f'{lt}/languages') as response:
                ok = response.status < 400
            latency_ms = int((time.perf_counter() - t0) * 1000)
        checks.append(
            {
                'id': 'libretranslate',
                'label': 'LibreTranslate',
                'status': 'healthy' if ok else 'degraded',
                'latency_ms': latency_ms,
            }
        )
    except Exception as exc:
        checks.append(
            {'id': 'libretranslate', 'label': 'LibreTranslate', 'status': 'offline', 'detail': str(exc)}
        )

    checks.append(
        {
            'id': 'open-webui',
            'label': 'Open WebUI',
            'status': 'healthy',
            'detail': 'API reachable',
        }
    )

    overall = health_status_from_checks(checks)
    return {'status': overall, 'checks': checks, 'checked_at': int(time.time())}


@router.post('/warmup')
async def model_warmup_manager(form_data: WarmupRequest, user=Depends(get_admin_user)):
    plan = warmup_plan(form_data.model_ids, max_warm=form_data.max_warm)
    results = []
    if form_data.execute and plan['selected']:
        base = await _ollama_base()
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            for model_id in plan['selected']:
                try:
                    async with session.post(
                        f'{base}/api/generate',
                        json={
                            'model': model_id,
                            'prompt': ' ',
                            'stream': False,
                            'keep_alive': -1,
                            'options': {'num_predict': 1},
                        },
                    ) as response:
                        ok = response.status < 400
                    results.append({'model': model_id, 'warmed': ok})
                except Exception as exc:
                    results.append({'model': model_id, 'warmed': False, 'error': str(exc)})
    return {'plan': plan, 'executed': bool(form_data.execute), 'results': results}


@router.get('/updates')
async def model_update_checker(user=Depends(get_admin_user)):
    try:
        models = await _fetch_ollama_tags()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {
        'models': [
            {
                'id': m.get('id'),
                'digest': m.get('digest'),
                'modified_at': m.get('modified_at'),
                'update_available': None,
            }
            for m in models
        ],
        'notes': 'Diagnostic listing only. No automatic model pulls.',
    }


@router.post('/benchmark')
async def local_model_benchmark(form_data: BenchmarkRequest, user=Depends(get_admin_user)):
    base = await _ollama_base()
    timeout = aiohttp.ClientTimeout(total=180)
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.post(
                f'{base}/api/generate',
                json={
                    'model': form_data.model,
                    'prompt': form_data.prompt,
                    'stream': False,
                    'options': {'num_predict': form_data.max_tokens},
                },
            ) as response:
                response.raise_for_status()
                data = await response.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    elapsed = time.perf_counter() - t0
    eval_count = int(data.get('eval_count') or 0)
    eval_duration = float(data.get('eval_duration') or 0) / 1e9
    prompt_eval = float(data.get('prompt_eval_duration') or 0) / 1e9
    tokens_per_sec = (eval_count / eval_duration) if eval_duration > 0 else None
    return {
        'model': form_data.model,
        'elapsed_sec': round(elapsed, 3),
        'prompt_eval_sec': round(prompt_eval, 3) if prompt_eval else None,
        'eval_count': eval_count,
        'tokens_per_sec': round(tokens_per_sec, 2) if tokens_per_sec else None,
        'sample': (data.get('response') or '')[:300],
        'disclaimer': 'Technical sample only — not a claim of model intelligence ranking.',
    }

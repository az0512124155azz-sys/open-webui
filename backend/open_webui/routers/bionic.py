"""Bionic model repository – OpenAI-compatible listing."""

from __future__ import annotations

import os
from typing import Any

import aiohttp
from fastapi import APIRouter, Depends
from open_webui.utils.auth import get_verified_user

router = APIRouter()


def _base() -> str:
    return (os.getenv('BIONIC_API_BASE') or os.getenv('BIONIC_BASE_URL') or '').rstrip('/')


@router.get('/status')
async def bionic_status(user=Depends(get_verified_user)):
    base = _base()
    return {
        'configured': bool(base),
        'base': base or None,
        'hint': 'Set BIONIC_API_BASE to an OpenAI-compatible /v1 endpoint',
    }


@router.get('/models')
async def bionic_models(user=Depends(get_verified_user)):
    base = _base()
    if not base:
        return {
            'object': 'list',
            'data': [],
            'error': 'BIONIC_API_BASE not set',
            'hint': 'Example: BIONIC_API_BASE=https://api.example.com/v1',
        }
    headers: dict[str, str] = {'Accept': 'application/json'}
    key = os.getenv('BIONIC_API_KEY') or os.getenv('BIONIC_TOKEN')
    if key:
        headers['Authorization'] = f'Bearer {key}'
    url = f'{base}/models'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    return {'object': 'list', 'data': [], 'error': f'HTTP {resp.status}', 'body': text[:500]}
                data = await resp.json(content_type=None)
    except Exception as exc:
        return {'object': 'list', 'data': [], 'error': str(exc)}
    items: list[dict[str, Any]] = []
    raw = data.get('data') if isinstance(data, dict) else data
    if isinstance(raw, list):
        for m in raw:
            if isinstance(m, dict):
                mid = m.get('id') or m.get('name') or m.get('model')
                if mid:
                    items.append({**m, 'id': mid, 'owned_by': m.get('owned_by') or 'bionic', 'source': 'bionic'})
    return {'object': 'list', 'data': items, 'source': 'bionic'}

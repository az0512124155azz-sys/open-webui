"""Stage 10 – Global Search + Offline-first API."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from open_webui.models.chats import Chats
from open_webui.utils.auth import get_verified_user
from open_webui.utils.search_offline import offline_status, search_rank
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter()


class SearchForm(BaseModel):
    query: str
    scope: list[str] = Field(default_factory=lambda: ['chats', 'messages'])
    limit: int = 30


class OfflineProbeForm(BaseModel):
    ollama_reachable: Optional[bool] = None
    libretranslate_reachable: Optional[bool] = None
    cloud_openai_reachable: Optional[bool] = None


@router.post('/search')
async def global_search(form_data: SearchForm, user=Depends(get_verified_user)):
    q = (form_data.query or '').strip()
    if not q or len(q) < 2:
        return {'query': q, 'results': [], 'count': 0}

    limit = max(1, min(form_data.limit, 100))
    results: list[dict[str, Any]] = []

    if 'chats' in form_data.scope or 'messages' in form_data.scope:
        try:
            chats = await Chats.get_chat_list_by_user_id(user.id, skip=0, limit=200)
        except Exception:
            try:
                chats = await Chats.get_chats_by_user_id(user.id)
            except Exception:
                chats = []

        for chat in chats or []:
            chat_id = getattr(chat, 'id', None) or (chat.get('id') if isinstance(chat, dict) else None)
            title = getattr(chat, 'title', None)
            if title is None and isinstance(chat, dict):
                title = (chat.get('chat') or {}).get('title') or chat.get('title') or ''
            title = str(title or '')

            score = search_rank(q, title)
            if score > 0 and 'chats' in form_data.scope:
                results.append(
                    {
                        'type': 'chat',
                        'id': chat_id,
                        'title': title,
                        'snippet': title[:200],
                        'score': score,
                    }
                )

            if 'messages' in form_data.scope and score < 80:
                payload = getattr(chat, 'chat', None)
                if payload is None and isinstance(chat, dict):
                    payload = chat.get('chat')
                history = (payload or {}).get('history') if isinstance(payload, dict) else None
                messages = (history or {}).get('messages') if isinstance(history, dict) else None
                if isinstance(messages, dict):
                    for mid, msg in list(messages.items())[:50]:
                        content = msg.get('content') if isinstance(msg, dict) else ''
                        if not isinstance(content, str):
                            content = str(content or '')
                        ms = search_rank(q, content)
                        if ms > 15:
                            results.append(
                                {
                                    'type': 'message',
                                    'id': mid,
                                    'chat_id': chat_id,
                                    'title': title,
                                    'snippet': content[:240],
                                    'score': ms,
                                }
                            )

    results.sort(key=lambda r: r.get('score', 0), reverse=True)
    results = results[:limit]
    return {'query': q, 'results': results, 'count': len(results), 'scope': form_data.scope}


@router.get('/offline/status')
async def get_offline_status(request: Request, user=Depends(get_verified_user)):
    ollama_models = getattr(request.app.state, 'OLLAMA_MODELS', None) or {}
    ollama_ok = bool(ollama_models) if ollama_models is not None else None
    return offline_status(ollama_reachable=ollama_ok)


@router.post('/offline/status')
async def post_offline_status(form_data: OfflineProbeForm, user=Depends(get_verified_user)):
    return offline_status(
        ollama_reachable=form_data.ollama_reachable,
        libretranslate_reachable=form_data.libretranslate_reachable,
        cloud_openai_reachable=form_data.cloud_openai_reachable,
    )

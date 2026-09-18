"""Stage 7 – Advanced Chat Intelligence API."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.constants import ERROR_MESSAGES
from open_webui.internal.db import get_async_session
from open_webui.models.chats import Chats
from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat_id import is_saved_chat_id
from open_webui.utils.chat_intelligence import (
    build_session_snapshot,
    merge_answers,
    optimize_context,
    prompt_version_record,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)
router = APIRouter()

_PROMPT_VERSIONS: dict[str, list[dict[str, Any]]] = {}
_SNAPSHOTS: dict[str, list[dict[str, Any]]] = {}


class ContextOptimizeForm(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    memories: list[dict[str, Any]] = Field(default_factory=list)
    files: list[dict[str, Any]] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)
    token_budget: int = 6000
    keep_recent: int = 12


class MergeAnswersForm(BaseModel):
    answers: list[dict[str, Any]] = Field(default_factory=list)
    strategy: str = 'concat'


class PromptVersionForm(BaseModel):
    prompt_id: str
    content: str
    title: Optional[str] = None


class SnapshotCreateForm(BaseModel):
    chat_id: str
    label: Optional[str] = None
    include_messages: bool = True


@router.post('/context/optimize')
async def context_optimize(form_data: ContextOptimizeForm, user=Depends(get_verified_user)):
    return optimize_context(
        form_data.messages,
        memories=form_data.memories,
        files=form_data.files,
        summaries=form_data.summaries,
        token_budget=max(500, min(form_data.token_budget, 128000)),
        keep_recent=max(2, min(form_data.keep_recent, 100)),
    )


@router.post('/answers/merge')
async def answers_merge(form_data: MergeAnswersForm, user=Depends(get_verified_user)):
    if form_data.strategy not in {'concat', 'first', 'vote_length'}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid strategy')
    return merge_answers(form_data.answers, strategy=form_data.strategy)


@router.post('/prompts/versions')
async def save_prompt_version(form_data: PromptVersionForm, user=Depends(get_verified_user)):
    versions = _PROMPT_VERSIONS.setdefault(form_data.prompt_id, [])
    record = prompt_version_record(
        form_data.prompt_id,
        form_data.content,
        title=form_data.title,
        user_id=user.id,
        version=len(versions) + 1,
    )
    versions.append(record)
    if len(versions) > 50:
        del versions[:-50]
    return record


@router.get('/prompts/{prompt_id}/versions')
async def list_prompt_versions(prompt_id: str, user=Depends(get_verified_user)):
    versions = _PROMPT_VERSIONS.get(prompt_id, [])
    visible = [
        v for v in versions if not v.get('user_id') or v.get('user_id') == user.id or user.role == 'admin'
    ]
    return {'prompt_id': prompt_id, 'versions': visible, 'count': len(visible)}


@router.get('/prompts/{prompt_id}/versions/{version}')
async def get_prompt_version(prompt_id: str, version: int, user=Depends(get_verified_user)):
    for item in _PROMPT_VERSIONS.get(prompt_id, []):
        if item.get('version') == version and (
            not item.get('user_id') or item.get('user_id') == user.id or user.role == 'admin'
        ):
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)


@router.post('/snapshots')
async def create_snapshot(
    form_data: SnapshotCreateForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    if not is_saved_chat_id(form_data.chat_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Only saved chats can be snapshotted'
        )

    chat = await Chats.get_chat_by_id(form_data.chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    if chat.user_id != user.id and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERROR_MESSAGES.UNAUTHORIZED)

    chat_data = chat.chat if isinstance(chat.chat, dict) else {}
    if not chat_data.get('id'):
        chat_data = {**chat_data, 'id': form_data.chat_id}

    snap = build_session_snapshot(
        chat_data,
        label=form_data.label,
        include_messages=form_data.include_messages,
    )
    snap['user_id'] = user.id
    bucket = _SNAPSHOTS.setdefault(form_data.chat_id, [])
    bucket.append(snap)
    if len(bucket) > 30:
        del bucket[:-30]
    return snap


@router.get('/snapshots/{chat_id}')
async def list_snapshots(chat_id: str, user=Depends(get_verified_user)):
    items = [
        s for s in _SNAPSHOTS.get(chat_id, []) if s.get('user_id') == user.id or user.role == 'admin'
    ]
    light = []
    for s in items:
        light.append(
            {
                'id': s.get('id'),
                'chat_id': s.get('chat_id'),
                'label': s.get('label'),
                'title': s.get('title'),
                'message_count': s.get('message_count'),
                'created_at': s.get('created_at'),
            }
        )
    return {'chat_id': chat_id, 'snapshots': light, 'count': len(light)}


@router.get('/snapshots/{chat_id}/{snapshot_id}')
async def get_snapshot(chat_id: str, snapshot_id: str, user=Depends(get_verified_user)):
    for s in _SNAPSHOTS.get(chat_id, []):
        if s.get('id') == snapshot_id and (s.get('user_id') == user.id or user.role == 'admin'):
            return s
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)

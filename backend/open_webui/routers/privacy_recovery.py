"""Stage 8 – Temporary / Privacy / Recovery API."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SAFE_MODE
from open_webui.models.chats import ChatForm, Chats
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.chat_id import is_saved_chat_id, is_temporary_chat_id
from open_webui.utils.privacy_recovery import audit_event, list_audit, recovery_plan, safe_mode_status
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter()


class ConvertTempChatForm(BaseModel):
    chat: dict = Field(default_factory=dict)
    title: Optional[str] = None
    folder_id: Optional[str] = None


class RecoveryForm(BaseModel):
    issue: str = 'unknown'


class AuditForm(BaseModel):
    action: str
    subject_type: Optional[str] = None
    subject_id: Optional[str] = None
    data: Optional[dict] = None


@router.get('/safe-mode')
async def get_safe_mode(user=Depends(get_verified_user)):
    return safe_mode_status(SAFE_MODE)


@router.get('/temporary/policy')
async def temporary_chat_policy(user=Depends(get_verified_user)):
    return {
        'default': {
            'persisted_to_history': False,
            'creates_memory': False,
            'long_term_memory': False,
        },
        'convert_to_normal': {
            'endpoint': 'POST /api/v1/privacy/temporary/convert',
            'requires_explicit_action': True,
        },
        'note': 'Upstream already supports temporary chat IDs; this documents policy and convert path.',
    }


@router.post('/temporary/convert')
async def convert_temporary_to_saved(form_data: ConvertTempChatForm, user=Depends(get_verified_user)):
    import uuid

    chat_body = dict(form_data.chat or {})
    chat_id = chat_body.get('id')
    if chat_id and is_saved_chat_id(str(chat_id)) and not is_temporary_chat_id(str(chat_id)):
        existing = await Chats.get_chat_by_id(str(chat_id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Chat is already saved',
            )

    if form_data.title:
        chat_body['title'] = form_data.title
    if not chat_body.get('title'):
        chat_body['title'] = 'Converted Chat'

    new_id = str(uuid.uuid4())
    chat_body['id'] = new_id

    try:
        result = await Chats.insert_new_chat(
            new_id,
            user.id,
            ChatForm(chat=chat_body, folder_id=form_data.folder_id),
        )
    except Exception as e:
        log.exception('convert temporary chat failed')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    audit_event(
        'temporary_chat.converted',
        actor_id=user.id,
        subject_type='chat',
        subject_id=new_id,
    )
    return {'status': True, 'chat': result, 'chat_id': new_id}


@router.get('/audit')
async def get_audit_log(
    limit: int = 50,
    action_prefix: Optional[str] = None,
    user=Depends(get_admin_user),
):
    return {'events': list_audit(limit=limit, action_prefix=action_prefix), 'limit': limit}


@router.post('/audit')
async def post_audit_event(form_data: AuditForm, user=Depends(get_admin_user)):
    entry = audit_event(
        form_data.action,
        actor_id=user.id,
        subject_type=form_data.subject_type,
        subject_id=form_data.subject_id,
        data=form_data.data,
    )
    return entry


@router.post('/recovery/plan')
async def get_recovery_plan(form_data: RecoveryForm, user=Depends(get_verified_user)):
    plan = recovery_plan(form_data.issue)
    audit_event(
        'recovery.plan_requested',
        actor_id=user.id,
        data={'issue': form_data.issue, 'destructive': plan.get('destructive')},
    )
    return plan

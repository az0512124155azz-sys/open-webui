"""Skills Platform extensions: AI draft generation and duplicate.

Keeps Stage 4/5 additions isolated from the large upstream skills router.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.constants import ERROR_MESSAGES
from open_webui.events import EVENTS, publish_event
from open_webui.internal.db import get_async_session
from open_webui.models.config import Config
from open_webui.models.skills import SkillForm, SkillMeta, Skills
from open_webui.utils.access_control import has_permission
from open_webui.utils.auth import get_verified_user
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)
router = APIRouter()

_ID_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{1,63}$')


class SkillGenerateForm(BaseModel):
    prompt: str = Field(min_length=8, max_length=4000)
    model: Optional[str] = None
    language: str = 'he'


class SkillDuplicateForm(BaseModel):
    id: str
    name: Optional[str] = None


def _slugify(value: str) -> str:
    value = re.sub(r'[^a-zA-Z0-9_-]+', '-', value.strip().lower())
    value = re.sub(r'-{2,}', '-', value).strip('-_')
    if not value:
        value = f'skill-{int(time.time())}'
    if value[0].isdigit():
        value = f's-{value}'
    return value[:64]


async def _generate_with_ollama(prompt: str, model: str, language: str) -> dict:
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434').split(';')[0].rstrip('/')
    system = (
        'You create reusable AI Skills for Open WebUI. '
        'Return ONLY valid JSON with keys: id, name, description, content, examples. '
        'content must be detailed markdown instructions the model should follow. '
        'id must be a short slug. Do not enable or save anything.'
    )
    if language.startswith('he'):
        system += ' Prefer Hebrew for name/description/content when the user wrote in Hebrew.'

    user_prompt = (
        f'Create a skill from this request:\n{prompt}\n\n'
        'JSON schema example:\n'
        '{"id":"android-fix","name":"Android Fix Helper","description":"...",'
        '"content":"...","examples":["..."]}'
    )
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        async with session.post(
            f'{base_url}/api/generate',
            json={
                'model': model,
                'prompt': f'{system}\n\n{user_prompt}',
                'stream': False,
                'keep_alive': -1,
                'format': 'json',
            },
        ) as response:
            response.raise_for_status()
            data = await response.json()
            raw = data.get('response') or ''
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            raise RuntimeError('Model did not return JSON skill draft')
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise RuntimeError('Skill draft JSON must be an object')
    return parsed


@router.post('/generate')
async def generate_skill_draft(
    form_data: SkillGenerateForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a Skill draft with a local model. Never auto-saves or enables."""
    if not (
        user.role == 'admin'
        or await has_permission(user.id, 'workspace.skills', await Config.get('user.permissions'), db=db)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERROR_MESSAGES.UNAUTHORIZED)

    model = (form_data.model or os.getenv('SKILL_GENERATE_MODEL') or 'qwen2.5:3b').strip()
    try:
        parsed = await _generate_with_ollama(form_data.prompt, model, form_data.language)
    except Exception as exc:
        log.exception('Skill generation failed')
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Unable to generate skill draft from local model: {exc}',
        ) from exc

    skill_id = _slugify(str(parsed.get('id') or parsed.get('name') or form_data.prompt[:40]))
    name = str(parsed.get('name') or skill_id).strip() or skill_id
    description = str(parsed.get('description') or '').strip()
    content = str(parsed.get('content') or '').strip()
    examples = parsed.get('examples') or []
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Generated skill is missing instructions content',
        )

    draft = {
        'id': skill_id,
        'name': name,
        'description': description,
        'content': content,
        'examples': examples if isinstance(examples, list) else [str(examples)],
        'is_active': False,
        'source_prompt': form_data.prompt,
        'model': model,
        'requires_user_confirmation': True,
        'notes': 'Draft only. Review, edit, save, then optionally enable.',
    }
    return {'draft': draft, 'saved': False, 'enabled': False}


@router.post('/id/{skill_id}/duplicate')
async def duplicate_skill(
    request: Request,
    skill_id: str,
    form_data: SkillDuplicateForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    if not (
        user.role == 'admin'
        or await has_permission(user.id, 'workspace.skills', await Config.get('user.permissions'), db=db)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERROR_MESSAGES.UNAUTHORIZED)

    source = await Skills.get_skill_by_id(skill_id, db=db)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)

    new_id = _slugify(form_data.id)
    if not _ID_RE.match(new_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid skill id')
    if await Skills.get_skill_by_id(new_id, db=db):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.ID_TAKEN)

    meta = source.meta.model_dump() if hasattr(source.meta, 'model_dump') else (source.meta or {})
    form = SkillForm(
        id=new_id,
        name=form_data.name or f'{source.name} (copy)',
        description=source.description,
        content=source.content,
        meta=SkillMeta(**meta) if isinstance(meta, dict) else SkillMeta(),
        is_active=False,
        access_grants=[],
    )
    skill = await Skills.insert_new_skill(user.id, form, db=db)
    if not skill:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.DEFAULT())
    await publish_event(
        request,
        EVENTS.SKILL_CREATED,
        actor=user,
        subject_id=skill.id,
        data={'name': skill.name, 'duplicated_from': skill_id},
    )
    return skill

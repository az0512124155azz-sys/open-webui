import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.config import BYPASS_ADMIN_ACCESS_CONTROL
from open_webui.constants import ERROR_MESSAGES
from open_webui.events import EVENTS, publish_event
from open_webui.internal.db import get_async_session
from open_webui.models.access_grants import AccessGrants
from open_webui.models.config import Config
from open_webui.models.groups import Groups
from open_webui.models.skills import (
    SkillAccessListResponse,
    SkillAccessResponse,
    SkillForm,
    SkillModel,
    SkillResponse,
    Skills,
    SkillUserResponse,
)
from open_webui.utils.access_control import filter_allowed_access_grants, has_permission
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.seed_default_skills import ensure_default_skills
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

PAGE_ITEM_COUNT = 30

router = APIRouter()


@router.get('/', response_model=list[SkillUserResponse])
async def get_skills(
    request: Request,
    query: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    await ensure_default_skills(user, db=db)
    if user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL:
        skills = await Skills.get_skills(db=db)
    else:
        skills = await Skills.get_skills(db=db, user_id=user.id)

    if query:
        q = query.casefold()
        skills = [skill for skill in skills if q in (skill.name or '').casefold()]

    return skills

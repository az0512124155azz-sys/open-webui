from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.internal.db import get_async_session
from open_webui.models.config import Config
from open_webui.routers import chats_legacy as _legacy
from open_webui.utils.auth import get_verified_user
from open_webui.utils.memory_chat_links import (
    count_memories_by_source_chat_id,
    delete_all_chat_linked_memories_for_user,
    delete_memories_for_chat,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _user_setting_enabled(user) -> bool:
    """Return True when the user opted into chat→memory delete cascade.

    Open WebUI persists most UI toggles at the top level of ``user.settings``.
    We also accept a nested ``ui.deleteChatMemories`` value for compatibility
    with any older clients or manual config edits.
    """
    settings = getattr(user, 'settings', None)
    if hasattr(settings, 'model_dump'):
        settings = settings.model_dump()
    settings = settings if isinstance(settings, dict) else {}
    if settings.get('deleteChatMemories'):
        return True
    ui = settings.get('ui') if isinstance(settings.get('ui'), dict) else {}
    return bool(ui.get('deleteChatMemories', False))


async def _authorized_chat(id: str, user, db: AsyncSession):
    if user.role == 'admin':
        chat = await _legacy.Chats.get_chat_by_id(id, db=db)
    else:
        if not await _legacy.has_permission(user.id, 'chat.delete', await Config.get('user.permissions')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_legacy.ERROR_MESSAGES.ACCESS_PROHIBITED,
            )
        chat = await _legacy.Chats.get_chat_by_id_and_user_id(id, user.id, db=db)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_legacy.ERROR_MESSAGES.NOT_FOUND)
    return chat


async def _associated_chat_ids(chat) -> list[str]:
    child_ids = await _legacy.Chats.get_internal_chat_ids_by_parent_id(chat.id, chat.user_id)
    return [chat.id, *child_ids]


@router.get('/{id}/memories/count')
async def get_chat_memory_count(
    id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    chat = await _authorized_chat(id, user, db)
    chat_ids = await _associated_chat_ids(chat)
    counts = [await count_memories_by_source_chat_id(chat.user_id, chat_id) for chat_id in chat_ids]
    return {'count': sum(counts), 'chat_ids': chat_ids, 'cascade_enabled': _user_setting_enabled(user)}


async def _delete_chat_and_optionally_memories(
    request: Request,
    id: str,
    user,
    db: AsyncSession,
    *,
    force_memories: bool,
):
    chat = await _authorized_chat(id, user, db)
    chat_ids = await _associated_chat_ids(chat)
    cascade = force_memories or _user_setting_enabled(user)

    result = await _legacy.delete_chat_by_id(request, id, user, db)
    if result and cascade:
        for chat_id in chat_ids:
            await delete_memories_for_chat(chat.user_id, chat_id)
    return result


@router.delete('/{id}/with-memories', response_model=bool)
async def delete_chat_with_memories(
    request: Request,
    id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await _delete_chat_and_optionally_memories(request, id, user, db, force_memories=True)


@router.delete('/{id}', response_model=bool)
async def delete_chat_by_id(
    request: Request,
    id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await _delete_chat_and_optionally_memories(request, id, user, db, force_memories=False)


@router.delete('/', response_model=bool)
async def delete_all_user_chats(
    request: Request,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete all chats for the user, optionally cascading chat-linked memories."""
    result = await _legacy.delete_all_user_chats(request, user, db)
    if result and _user_setting_enabled(user):
        await delete_all_chat_linked_memories_for_user(user.id)
    return result


router.include_router(_legacy.router)


def __getattr__(name: str):
    return getattr(_legacy, name)

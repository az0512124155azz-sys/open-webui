from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from open_webui.routers import memories_legacy as _legacy
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.memory_chat_links import (
    bulk_delete_memories,
    link_created_memories_to_chat,
    list_all_memories_with_sources,
)

router = APIRouter()


@router.post('/update', response_model=list[dict])
async def update_memories(
    request: Request,
    form_data: _legacy.UpdateMemoriesForm,
    user=Depends(get_verified_user),
):
    response = await _legacy.update_memories(request, form_data, user)
    metadata = getattr(request.state, 'metadata', {}) or {}
    chat_id = metadata.get('chat_id')
    if chat_id:
        created_ids = [
            item.get('memory', {}).get('id')
            for item in response
            if item.get('status') == 'created' and isinstance(item.get('memory'), dict)
        ]
        await link_created_memories_to_chat(created_ids, user.id, chat_id)
    return response


class BulkDeleteMemoriesForm(BaseModel):
    ids: list[str]


@router.get('/admin/all')
async def admin_list_memories(user=Depends(get_admin_user)):
    return await list_all_memories_with_sources()


@router.get('/admin/export')
async def admin_export_memories(user=Depends(get_admin_user)):
    return {'memories': await list_all_memories_with_sources()}


@router.post('/admin/bulk-delete')
async def admin_bulk_delete_memories(
    form_data: BulkDeleteMemoriesForm,
    user=Depends(get_admin_user),
):
    return await bulk_delete_memories(form_data.ids)


# Keep all upstream routes after custom overrides so FastAPI resolves the custom
# /update handler first while the rest of the public surface remains unchanged.
router.include_router(_legacy.router)


def __getattr__(name: str):
    return getattr(_legacy, name)

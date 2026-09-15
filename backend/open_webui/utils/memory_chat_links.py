from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from open_webui.internal.db import get_async_db_context
from open_webui.retrieval.vector.async_client import ASYNC_VECTOR_DB_CLIENT
from sqlalchemy import JSON, BigInteger, Column, MetaData, String, Table, Text, delete, select, update

_metadata = MetaData()
_memory = Table(
    'memory',
    _metadata,
    Column('id', String, primary_key=True),
    Column('user_id', String),
    Column('type', String),
    Column('path', Text),
    Column('content', Text),
    Column('meta', JSON),
    Column('source_chat_id', String),
    Column('updated_at', BigInteger),
    Column('created_at', BigInteger),
)


def _row_dict(row) -> dict:
    return dict(row._mapping)


async def link_created_memories_to_chat(memory_ids: Iterable[str], user_id: str, chat_id: str | None) -> int:
    ids = [memory_id for memory_id in memory_ids if memory_id]
    if not ids or not chat_id:
        return 0
    async with get_async_db_context() as db:
        result = await db.execute(
            update(_memory)
            .where(_memory.c.id.in_(ids))
            .where(_memory.c.user_id == user_id)
            .where(_memory.c.source_chat_id.is_(None))
            .values(source_chat_id=chat_id)
        )
        await db.commit()
        return int(result.rowcount or 0)


async def get_memories_by_source_chat_id(user_id: str, chat_id: str) -> list[dict]:
    async with get_async_db_context() as db:
        result = await db.execute(
            select(_memory).where(_memory.c.user_id == user_id).where(_memory.c.source_chat_id == chat_id)
        )
        return [_row_dict(row) for row in result.fetchall()]


async def count_memories_by_source_chat_id(user_id: str, chat_id: str) -> int:
    return len(await get_memories_by_source_chat_id(user_id, chat_id))


async def delete_memories_for_chat(user_id: str, chat_id: str) -> dict:
    rows = await get_memories_by_source_chat_id(user_id, chat_id)
    ids = [row['id'] for row in rows]
    if not ids:
        return {'count': 0, 'ids': []}

    async with get_async_db_context() as db:
        await db.execute(delete(_memory).where(_memory.c.user_id == user_id).where(_memory.c.source_chat_id == chat_id))
        await db.commit()

    try:
        await ASYNC_VECTOR_DB_CLIENT.delete(collection_name=f'user-memory-{user_id}', ids=ids)
    except Exception:
        # SQL deletion is authoritative. A subsequent memory reindex removes
        # stale vectors if a vector backend is temporarily unavailable.
        pass
    return {'count': len(ids), 'ids': ids}


async def list_all_memories_with_sources() -> list[dict]:
    async with get_async_db_context() as db:
        result = await db.execute(select(_memory).order_by(_memory.c.created_at.desc()))
        return [_row_dict(row) for row in result.fetchall()]


async def bulk_delete_memories(memory_ids: Iterable[str]) -> dict:
    ids = list(dict.fromkeys(memory_id for memory_id in memory_ids if memory_id))
    if not ids:
        return {'count': 0, 'ids': []}

    async with get_async_db_context() as db:
        rows = (await db.execute(select(_memory).where(_memory.c.id.in_(ids)))).fetchall()
        records = [_row_dict(row) for row in rows]
        await db.execute(delete(_memory).where(_memory.c.id.in_(ids)))
        await db.commit()

    by_user: dict[str, list[str]] = defaultdict(list)
    for record in records:
        by_user[record['user_id']].append(record['id'])
    for user_id, vector_ids in by_user.items():
        try:
            await ASYNC_VECTOR_DB_CLIENT.delete(collection_name=f'user-memory-{user_id}', ids=vector_ids)
        except Exception:
            pass

    deleted_ids = [record['id'] for record in records]
    return {'count': len(deleted_ids), 'ids': deleted_ids}

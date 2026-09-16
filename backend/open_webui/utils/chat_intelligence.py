"""Stage 7 – Advanced Chat Intelligence helpers.

Context optimization, prompt versioning structures, session snapshots,
and optional multi-answer merge — without deleting real chat history.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _msg_text(message: dict[str, Any]) -> str:
    content = message.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                parts.append(str(item.get('text') or ''))
            elif isinstance(item, str):
                parts.append(item)
        return '\n'.join(parts)
    return str(content or '')


def optimize_context(
    messages: list[dict[str, Any]],
    *,
    memories: list[dict[str, Any]] | None = None,
    files: list[dict[str, Any]] | None = None,
    summaries: list[str] | None = None,
    token_budget: int = 6000,
    keep_recent: int = 12,
) -> dict[str, Any]:
    memories = memories or []
    files = files or []
    summaries = summaries or []

    recent = messages[-keep_recent:] if messages else []
    older = messages[:-keep_recent] if len(messages) > keep_recent else []

    pack: list[dict[str, Any]] = []
    used = 0
    dropped = 0

    def try_add(kind: str, payload: dict[str, Any], text: str) -> bool:
        nonlocal used, dropped
        cost = estimate_tokens(text)
        if used + cost > token_budget and pack:
            dropped += 1
            return False
        pack.append({'kind': kind, 'tokens': cost, **payload})
        used += cost
        return True

    for summary in summaries:
        try_add('summary', {'text': summary}, summary)

    for mem in memories[:20]:
        body = str(mem.get('content') or mem.get('text') or '')
        if body:
            try_add('memory', {'id': mem.get('id'), 'text': body}, body)

    for f in files[:15]:
        name = str(f.get('name') or f.get('filename') or f.get('id') or 'file')
        snippet = str(f.get('snippet') or f.get('content') or '')[:1500]
        text = f'{name}\n{snippet}'.strip()
        if text:
            try_add('file', {'id': f.get('id'), 'name': name, 'text': snippet}, text)

    recent_block: list[dict[str, Any]] = []
    recent_tokens = 0
    for msg in reversed(recent):
        text = _msg_text(msg)
        cost = estimate_tokens(text)
        if recent_tokens + cost > max(token_budget // 2, token_budget - used) and recent_block:
            dropped += 1
            continue
        recent_block.append(
            {
                'kind': 'message',
                'role': msg.get('role'),
                'id': msg.get('id'),
                'text': text,
                'tokens': cost,
            }
        )
        recent_tokens += cost
    recent_block.reverse()
    pack.extend(recent_block)
    used += recent_tokens

    return {
        'token_budget': token_budget,
        'tokens_used': used,
        'items': pack,
        'stats': {
            'messages_total': len(messages),
            'messages_in_pack': len(recent_block),
            'older_not_in_pack': len(older),
            'memories': sum(1 for i in pack if i['kind'] == 'memory'),
            'files': sum(1 for i in pack if i['kind'] == 'file'),
            'summaries': sum(1 for i in pack if i['kind'] == 'summary'),
            'dropped_items': dropped,
        },
        'note': 'View only — original chat history is not deleted.',
    }


def merge_answers(answers: list[dict[str, Any]], strategy: str = 'concat') -> dict[str, Any]:
    cleaned = []
    for item in answers:
        model = str(item.get('model') or item.get('id') or 'model')
        content = str(item.get('content') or item.get('text') or '').strip()
        if content:
            cleaned.append({'model': model, 'content': content})

    if not cleaned:
        return {'merged': '', 'sources': [], 'strategy': strategy}

    if strategy == 'first':
        merged = cleaned[0]['content']
    elif strategy == 'vote_length':
        merged = max(cleaned, key=lambda a: len(a['content']))['content']
    else:
        parts = [f"### {a['model']}\n{a['content']}" for a in cleaned]
        merged = '\n\n'.join(parts)

    return {
        'merged': merged,
        'sources': cleaned,
        'strategy': strategy,
        'note': 'Original answers preserved in sources.',
    }


def prompt_version_record(
    prompt_id: str,
    content: str,
    *,
    title: str | None = None,
    user_id: str | None = None,
    version: int | None = None,
) -> dict[str, Any]:
    digest = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    return {
        'prompt_id': prompt_id,
        'version': version or int(time.time()),
        'title': title or '',
        'content': content,
        'content_hash': digest,
        'user_id': user_id,
        'created_at': int(time.time()),
    }


def build_session_snapshot(
    chat: dict[str, Any],
    *,
    label: str | None = None,
    include_messages: bool = True,
) -> dict[str, Any]:
    history = chat.get('history') or {}
    messages = history.get('messages') if isinstance(history, dict) else {}
    if isinstance(messages, dict):
        msg_list = list(messages.values())
    elif isinstance(messages, list):
        msg_list = messages
    else:
        msg_list = []

    payload = {
        'id': f"snap-{int(time.time())}-{hashlib.sha256(str(chat.get('id')).encode()).hexdigest()[:8]}",
        'chat_id': chat.get('id'),
        'label': label or f"Snapshot {time.strftime('%Y-%m-%d %H:%M')}",
        'title': chat.get('title'),
        'models': chat.get('models'),
        'created_at': int(time.time()),
        'message_count': len(msg_list),
        'current_id': history.get('currentId') if isinstance(history, dict) else None,
    }
    if include_messages:
        payload['history'] = history
        payload['messages'] = msg_list
    return payload

"""Stage 8 – Temporary chats helpers, Safe Mode status, audit log, recovery."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

_AUDIT: deque[dict[str, Any]] = deque(maxlen=500)


def audit_event(
    action: str,
    *,
    actor_id: str | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_data: dict[str, Any] = {}
    if data:
        for k, v in data.items():
            key = str(k).lower()
            if any(s in key for s in ('password', 'secret', 'token', 'api_key', 'apikey', 'authorization')):
                safe_data[k] = '[redacted]'
            else:
                safe_data[k] = v

    entry = {
        'id': f'aud-{int(time.time() * 1000)}-{len(_AUDIT)}',
        'action': action,
        'actor_id': actor_id,
        'subject_type': subject_type,
        'subject_id': subject_id,
        'data': safe_data,
        'ts': int(time.time()),
    }
    _AUDIT.appendleft(entry)
    return entry


def list_audit(limit: int = 50, action_prefix: str | None = None) -> list[dict[str, Any]]:
    items = list(_AUDIT)
    if action_prefix:
        items = [e for e in items if str(e.get('action', '')).startswith(action_prefix)]
    return items[: max(1, min(limit, 200))]


def safe_mode_status(env_safe_mode: bool) -> dict[str, Any]:
    return {
        'enabled': bool(env_safe_mode),
        'disables': [
            'plugins (custom)',
            'custom filters/functions (deactivated on boot when SAFE_MODE)',
            'optional integrations may be skipped',
        ],
        'preserves': [
            'configuration is not deleted',
            'core Open WebUI routes remain available',
        ],
        'note': 'Set SAFE_MODE=true in environment and restart to enable.',
    }


def recovery_plan(issue: str) -> dict[str, Any]:
    issue = (issue or '').strip().lower()
    plans = {
        'plugin': {
            'steps': [
                'Disable the failing plugin via Admin → Plugins',
                'Or restart with SAFE_MODE=true',
                'Configuration is kept; nothing is deleted',
            ],
            'destructive': False,
        },
        'model': {
            'steps': [
                'Retry the model call',
                'Use model-intelligence fallback if configured',
                'Unload stuck Ollama models via /api/models/unload',
            ],
            'destructive': False,
        },
        'temporary_chat': {
            'steps': [
                'Temporary chats are not persisted by default',
                'Use Convert to normal chat only when the user confirms',
            ],
            'destructive': False,
        },
        'job': {
            'steps': [
                'Stop stuck tasks via /api/tasks/chat/{id}/stop',
                'Clear client cache / hard refresh if UI state is stale',
            ],
            'destructive': False,
        },
    }
    for key, plan in plans.items():
        if key in issue:
            return {'issue': issue, **plan}
    return {
        'issue': issue or 'unknown',
        'steps': [
            'Check /health and /ready',
            'Review audit log for recent admin actions',
            'Enable SAFE_MODE if custom extensions are suspected',
        ],
        'destructive': False,
    }

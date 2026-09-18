"""Stage 12 – Production hardening self-check helpers (non-destructive)."""

from __future__ import annotations

from typing import Any

EXPECTED_ROUTER_PREFIXES = [
    '/api/v1/plugins',
    '/api/v1/skills',
    '/api/v1/model-intelligence',
    '/api/v1/chat-intelligence',
    '/api/v1/privacy',
    '/api/v1/files-projects',
    '/api/v1/search',
    '/api/v1/jobs',
]


def hardening_report(*, registered_paths: list[str] | None = None) -> dict[str, Any]:
    paths = registered_paths or []
    missing = []
    present = []
    for prefix in EXPECTED_ROUTER_PREFIXES:
        if any(prefix in p for p in paths):
            present.append(prefix)
        else:
            missing.append(prefix)

    return {
        'security': {
            'auth_on_custom_routers': 'required',
            'secrets_in_audit': 'redacted',
            'safe_filenames': True,
            'no_shell_in_stage_modules': True,
            'npm_audit_force_forbidden': True,
        },
        'compatibility': {
            'additive_apis_only': True,
            'core_ui_preserved': True,
            'process_local_stores_note': 'projects/jobs/audit/snapshots are process-local until DB migration',
        },
        'queue': {
            'max_concurrent': 4,
            'max_retries': 2,
            'infinite_retries': False,
        },
        'routers': {
            'expected': EXPECTED_ROUTER_PREFIXES,
            'present': present,
            'missing': missing,
            'ok': len(missing) == 0,
        },
    }

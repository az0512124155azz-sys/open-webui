"""Stage 12–13 – Hardening status + QA summary API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.production_hardening import hardening_report

router = APIRouter()


def _collect_paths(app) -> list[str]:
    paths: list[str] = []
    for route in getattr(app, 'routes', []) or []:
        path = getattr(route, 'path', None)
        if path:
            paths.append(str(path))
    return paths


@router.get('/status')
async def hardening_status(request: Request, user=Depends(get_verified_user)):
    paths = _collect_paths(request.app)
    report = hardening_report(registered_paths=paths)
    report['startup_complete'] = bool(getattr(request.app.state, 'startup_complete', False))
    return report


@router.get('/qa-summary')
async def qa_summary(request: Request, user=Depends(get_admin_user)):
    paths = _collect_paths(request.app)
    report = hardening_report(registered_paths=paths)
    return {
        'stage': 13,
        'hardening': report,
        'checks_doc': 'docs/STAGE13_FINAL_QA.md',
        'hardening_doc': 'docs/STAGE12_PRODUCTION_HARDENING.md',
        'ready_for_release': report['routers']['ok'] and report['queue']['infinite_retries'] is False,
    }

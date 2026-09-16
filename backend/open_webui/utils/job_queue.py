"""Stage 11 – Lightweight job queue with priorities, cancel, limits, retry."""

from __future__ import annotations

import time
import uuid
from typing import Any

_JOBS: dict[str, dict[str, Any]] = {}
_MAX_CONCURRENT = 4
_MAX_RETRIES = 2


def create_job(
    *,
    kind: str,
    payload: dict[str, Any] | None = None,
    priority: int = 5,
    user_id: str | None = None,
    timeout_sec: int = 300,
) -> dict[str, Any]:
    jid = str(uuid.uuid4())
    job = {
        'id': jid,
        'kind': kind,
        'payload': payload or {},
        'priority': max(1, min(int(priority), 10)),
        'user_id': user_id,
        'status': 'queued',
        'retries': 0,
        'max_retries': _MAX_RETRIES,
        'timeout_sec': max(5, min(timeout_sec, 3600)),
        'created_at': int(time.time()),
        'updated_at': int(time.time()),
        'error': None,
        'result': None,
    }
    _JOBS[jid] = job
    _schedule()
    return job


def _running_count() -> int:
    return sum(1 for j in _JOBS.values() if j.get('status') == 'running')


def _schedule() -> None:
    queued = [j for j in _JOBS.values() if j.get('status') == 'queued']
    queued.sort(key=lambda j: (-j.get('priority', 5), j.get('created_at', 0)))
    for job in queued:
        if _running_count() >= _MAX_CONCURRENT:
            break
        job['status'] = 'running'
        job['updated_at'] = int(time.time())


def complete_job(job_id: str, result: Any = None) -> dict[str, Any] | None:
    job = _JOBS.get(job_id)
    if not job:
        return None
    if job.get('status') == 'cancelled':
        return job
    job['status'] = 'completed'
    job['result'] = result
    job['updated_at'] = int(time.time())
    _schedule()
    return job


def fail_job(job_id: str, error: str) -> dict[str, Any] | None:
    job = _JOBS.get(job_id)
    if not job:
        return None
    if job.get('status') == 'cancelled':
        return job
    job['retries'] = int(job.get('retries') or 0) + 1
    job['error'] = error
    job['updated_at'] = int(time.time())
    if job['retries'] <= job.get('max_retries', _MAX_RETRIES):
        job['status'] = 'queued'
    else:
        job['status'] = 'failed'
    _schedule()
    return job


def cancel_job(job_id: str) -> dict[str, Any] | None:
    job = _JOBS.get(job_id)
    if not job:
        return None
    if job.get('status') in ('completed', 'failed', 'cancelled'):
        return job
    job['status'] = 'cancelled'
    job['updated_at'] = int(time.time())
    _schedule()
    return job


def get_job(job_id: str) -> dict[str, Any] | None:
    return _JOBS.get(job_id)


def list_jobs(user_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    items = list(_JOBS.values())
    if user_id:
        items = [j for j in items if j.get('user_id') == user_id]
    items.sort(key=lambda j: j.get('updated_at', 0), reverse=True)
    return items[: max(1, min(limit, 200))]


def queue_stats() -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for j in _JOBS.values():
        s = str(j.get('status'))
        by_status[s] = by_status.get(s, 0) + 1
    return {
        'max_concurrent': _MAX_CONCURRENT,
        'max_retries': _MAX_RETRIES,
        'by_status': by_status,
        'total': len(_JOBS),
    }

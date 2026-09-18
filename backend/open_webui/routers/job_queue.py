"""Stage 11 – Job queue + orchestration API."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.utils.auth import get_verified_user
from open_webui.utils.job_queue import (
    cancel_job,
    complete_job,
    create_job,
    fail_job,
    get_job,
    list_jobs,
    queue_stats,
)
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter()


class CreateJobForm(BaseModel):
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 5
    timeout_sec: int = 300


class CompleteJobForm(BaseModel):
    result: Optional[Any] = None


class FailJobForm(BaseModel):
    error: str = 'failed'


@router.get('/stats')
async def stats(user=Depends(get_verified_user)):
    return queue_stats()


@router.get('/jobs')
async def jobs_list(limit: int = 50, user=Depends(get_verified_user)):
    items = list_jobs(user_id=None if user.role == 'admin' else user.id, limit=limit)
    return {'jobs': items, 'count': len(items)}


@router.post('/jobs')
async def jobs_create(form_data: CreateJobForm, user=Depends(get_verified_user)):
    job = create_job(
        kind=form_data.kind,
        payload=form_data.payload,
        priority=form_data.priority,
        user_id=user.id,
        timeout_sec=form_data.timeout_sec,
    )
    return job


@router.get('/jobs/{job_id}')
async def jobs_get(job_id: str, user=Depends(get_verified_user)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    if job.get('user_id') != user.id and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    return job


@router.post('/jobs/{job_id}/complete')
async def jobs_complete(job_id: str, form_data: CompleteJobForm, user=Depends(get_verified_user)):
    job = get_job(job_id)
    if not job or (job.get('user_id') != user.id and user.role != 'admin'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    return complete_job(job_id, form_data.result)


@router.post('/jobs/{job_id}/fail')
async def jobs_fail(job_id: str, form_data: FailJobForm, user=Depends(get_verified_user)):
    job = get_job(job_id)
    if not job or (job.get('user_id') != user.id and user.role != 'admin'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    return fail_job(job_id, form_data.error)


@router.post('/jobs/{job_id}/cancel')
async def jobs_cancel(job_id: str, user=Depends(get_verified_user)):
    job = get_job(job_id)
    if not job or (job.get('user_id') != user.id and user.role != 'admin'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    return cancel_job(job_id)

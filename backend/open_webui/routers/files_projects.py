"""Stage 9 – Files & Projects API."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends
from open_webui.utils.auth import get_verified_user
from open_webui.utils.files_projects import classify_file, project_bundle_schema, safe_filename
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter()

_PROJECTS: dict[str, dict[str, Any]] = {}


class ClassifyForm(BaseModel):
    filename: str
    content_type: Optional[str] = None


class ClassifyBatchForm(BaseModel):
    files: list[ClassifyForm] = Field(default_factory=list)


class ProjectForm(BaseModel):
    name: str
    description: str = ''
    chat_ids: list[str] = Field(default_factory=list)
    file_ids: list[str] = Field(default_factory=list)
    instructions: str = ''
    memory_ids: list[str] = Field(default_factory=list)
    model_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    plugin_ids: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chat_ids: Optional[list[str]] = None
    file_ids: Optional[list[str]] = None
    instructions: Optional[str] = None
    memory_ids: Optional[list[str]] = None
    model_ids: Optional[list[str]] = None
    skill_ids: Optional[list[str]] = None
    plugin_ids: Optional[list[str]] = None
    settings: Optional[dict[str, Any]] = None


class DownloadPackageForm(BaseModel):
    filenames: list[str] = Field(default_factory=list)
    note: str = 'Client resolves paths; server only returns safe names + classification.'


@router.post('/classify')
async def classify_one(form_data: ClassifyForm, user=Depends(get_verified_user)):
    return classify_file(form_data.filename, form_data.content_type)


@router.post('/classify/batch')
async def classify_batch(form_data: ClassifyBatchForm, user=Depends(get_verified_user)):
    results = [classify_file(f.filename, f.content_type) for f in form_data.files[:100]]
    return {'files': results, 'count': len(results)}


@router.get('/actions/{kind}')
async def actions_for_kind(kind: str, user=Depends(get_verified_user)):
    info = classify_file(f'file.{kind}' if '.' not in kind else f'x.{kind}')
    return {'kind': kind, 'actions': info['actions'], 'treatments': info['treatments']}


@router.post('/download-package/plan')
async def download_package_plan(form_data: DownloadPackageForm, user=Depends(get_verified_user)):
    items = []
    for name in form_data.filenames[:200]:
        safe = safe_filename(name)
        items.append({'requested': name, 'safe_name': safe, 'classification': classify_file(safe)})
    return {
        'items': items,
        'security': {'path_traversal_blocked': True, 'basename_only': True, 'max_files': 200},
        'note': form_data.note,
    }


@router.get('/projects/schema')
async def get_project_schema(user=Depends(get_verified_user)):
    return project_bundle_schema()


@router.get('/projects')
async def list_projects(user=Depends(get_verified_user)):
    items = [p for p in _PROJECTS.values() if p.get('user_id') == user.id or user.role == 'admin']
    return {'projects': items, 'count': len(items)}


@router.post('/projects')
async def create_project(form_data: ProjectForm, user=Depends(get_verified_user)):
    pid = str(uuid.uuid4())
    project = {
        'id': pid,
        'user_id': user.id,
        'name': form_data.name,
        'description': form_data.description,
        'chat_ids': form_data.chat_ids,
        'file_ids': form_data.file_ids,
        'instructions': form_data.instructions,
        'memory_ids': form_data.memory_ids,
        'model_ids': form_data.model_ids,
        'skill_ids': form_data.skill_ids,
        'plugin_ids': form_data.plugin_ids,
        'settings': form_data.settings,
        'created_at': int(time.time()),
        'updated_at': int(time.time()),
    }
    _PROJECTS[pid] = project
    return project


@router.get('/projects/{project_id}')
async def get_project(project_id: str, user=Depends(get_verified_user)):
    p = _PROJECTS.get(project_id)
    if not p or (p.get('user_id') != user.id and user.role != 'admin'):
        return {'error': 'not_found'}
    return p


@router.patch('/projects/{project_id}')
async def update_project(project_id: str, form_data: ProjectUpdateForm, user=Depends(get_verified_user)):
    p = _PROJECTS.get(project_id)
    if not p or (p.get('user_id') != user.id and user.role != 'admin'):
        return {'error': 'not_found'}
    data = form_data.model_dump(exclude_unset=True)
    p.update(data)
    p['updated_at'] = int(time.time())
    return p


@router.delete('/projects/{project_id}')
async def delete_project(project_id: str, user=Depends(get_verified_user)):
    p = _PROJECTS.get(project_id)
    if not p or (p.get('user_id') != user.id and user.role != 'admin'):
        return {'status': False, 'error': 'not_found'}
    del _PROJECTS[project_id]
    return {'status': True}

"""Plugins Platform API.

Exposes Open WebUI Functions as a first-class plugin registry with manifest
validation, permission visibility, and safe lifecycle operations.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.constants import ERROR_MESSAGES
from open_webui.events import EVENTS, publish_event
from open_webui.models.functions import FunctionForm, FunctionMeta, Functions
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.plugin import load_function_module_by_id
from open_webui.utils.plugin_registry import (
    PERMISSION_CATALOG,
    function_to_plugin_record,
    validate_plugin_manifest,
)
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter()


class PluginInstallForm(BaseModel):
    id: str
    name: str
    content: str
    type: str = 'filter'
    description: str = ''
    version: str = '1.0.0'
    author: str = ''
    icon: str = ''
    permissions: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    is_active: bool = False
    is_global: bool = False
    settings_schema: dict[str, Any] = Field(default_factory=dict)
    required_open_webui_version: str = ''


class PluginValidateForm(BaseModel):
    id: str = 'example_plugin'
    name: str = 'Example Plugin'
    content: str = ''
    type: str = 'filter'
    description: str = ''
    version: str = '1.0.0'
    author: str = ''
    permissions: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class PluginConfigureForm(BaseModel):
    valves: dict[str, Any] = Field(default_factory=dict)


def _manifest_dict(form: PluginInstallForm | PluginValidateForm) -> dict[str, Any]:
    return {
        'id': form.id,
        'name': form.name,
        'version': form.version,
        'description': form.description,
        'author': getattr(form, 'author', ''),
        'icon': getattr(form, 'icon', ''),
        'type': form.type,
        'permissions': form.permissions,
        'capabilities': form.capabilities,
        'settings_schema': getattr(form, 'settings_schema', {}),
        'required_open_webui_version': getattr(form, 'required_open_webui_version', ''),
    }


@router.get('/permissions')
async def list_plugin_permissions(user=Depends(get_verified_user)):
    return {'permissions': PERMISSION_CATALOG}


@router.get('/')
async def list_plugins(user=Depends(get_verified_user)):
    functions = await Functions.get_functions()
    return {'plugins': [function_to_plugin_record(item) for item in functions]}


@router.get('/id/{plugin_id}')
async def get_plugin(plugin_id: str, user=Depends(get_verified_user)):
    function = await Functions.get_function_by_id(plugin_id)
    if not function:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    return function_to_plugin_record(function)


@router.post('/validate')
async def validate_plugin(form_data: PluginValidateForm, user=Depends(get_verified_user)):
    result = validate_plugin_manifest(_manifest_dict(form_data), content=form_data.content)
    return result.model_dump()


@router.post('/install')
async def install_plugin(
    request: Request,
    form_data: PluginInstallForm,
    user=Depends(get_admin_user),
):
    validation = validate_plugin_manifest(_manifest_dict(form_data), content=form_data.content)
    if not validation.valid or validation.manifest is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'message': 'Invalid plugin manifest or source', 'errors': validation.errors},
        )

    existing = await Functions.get_function_by_id(form_data.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.ID_TAKEN)

    try:
        await load_function_module_by_id(form_data.id, content=form_data.content)
    except Exception as exc:
        log.exception('Plugin install rejected: failed to load module')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Plugin failed safe load: {exc}',
        ) from exc

    function_form = FunctionForm(
        id=form_data.id,
        name=form_data.name,
        content=form_data.content,
        meta=FunctionMeta(
            description=form_data.description,
            manifest=validation.manifest.model_dump(),
        ),
    )
    created = await Functions.insert_new_function(user.id, form_data.type, function_form)
    if not created:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.DEFAULT())

    if form_data.is_active:
        await Functions.update_function_by_id(form_data.id, {'is_active': True})
    if form_data.is_global:
        await Functions.update_function_by_id(form_data.id, {'is_global': True})

    await publish_event(
        request,
        EVENTS.FUNCTION_CREATED,
        actor=user,
        subject_id=form_data.id,
        data={'name': form_data.name, 'plugin': True},
    )
    function = await Functions.get_function_by_id(form_data.id)
    return function_to_plugin_record(function)


@router.post('/id/{plugin_id}/enable')
async def enable_plugin(plugin_id: str, user=Depends(get_admin_user)):
    function = await Functions.get_function_by_id(plugin_id)
    if not function:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    updated = await Functions.update_function_by_id(plugin_id, {'is_active': True})
    return function_to_plugin_record(updated or function)


@router.post('/id/{plugin_id}/disable')
async def disable_plugin(plugin_id: str, user=Depends(get_admin_user)):
    function = await Functions.get_function_by_id(plugin_id)
    if not function:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    updated = await Functions.update_function_by_id(plugin_id, {'is_active': False})
    return function_to_plugin_record(updated or function)


@router.post('/id/{plugin_id}/configure')
async def configure_plugin(
    plugin_id: str,
    form_data: PluginConfigureForm,
    user=Depends(get_admin_user),
):
    function = await Functions.get_function_by_id(plugin_id)
    if not function:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    updated = await Functions.update_function_by_id(plugin_id, {'valves': form_data.valves})
    return function_to_plugin_record(updated or function)


@router.delete('/id/{plugin_id}')
async def uninstall_plugin(request: Request, plugin_id: str, user=Depends(get_admin_user)):
    function = await Functions.get_function_by_id(plugin_id)
    if not function:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    await Functions.update_function_by_id(plugin_id, {'is_active': False})
    result = await Functions.delete_function_by_id(plugin_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.DEFAULT())
    return {'success': True, 'id': plugin_id}

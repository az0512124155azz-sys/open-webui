from __future__ import annotations

import ast
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

PLUGIN_PERMISSIONS = (
    'network',
    'chat.read',
    'chat.write',
    'files.read',
    'files.write',
    'tools.execute',
    'models.access',
    'memory.access',
)

PLUGIN_TYPES = ('filter', 'action', 'pipe', 'tool')

_ID_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{1,63}$')


class PluginManifest(BaseModel):
    id: str
    name: str
    version: str = '1.0.0'
    description: str = ''
    author: str = ''
    icon: str = ''
    type: Literal['filter', 'action', 'pipe', 'tool'] = 'filter'
    permissions: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    settings_schema: dict[str, Any] = Field(default_factory=dict)
    required_open_webui_version: str = ''
    capabilities: list[str] = Field(default_factory=list)

    @field_validator('id')
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not _ID_RE.match(value or ''):
            raise ValueError(
                'Plugin id must start with a letter and contain only letters, numbers, _ or - (2-64 chars)'
            )
        return value

    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, value: list[str]) -> list[str]:
        unknown = sorted({item for item in value if item not in PLUGIN_PERMISSIONS})
        if unknown:
            raise ValueError(f'Unknown plugin permissions: {", ".join(unknown)}')
        return list(dict.fromkeys(value))

    @field_validator('version')
    @classmethod
    def validate_version(cls, value: str) -> str:
        if not re.match(r'^\d+(\.\d+){0,3}([.-][a-zA-Z0-9]+)?$', value or ''):
            raise ValueError('version must look like 1.0.0')
        return value


class PluginValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manifest: PluginManifest | None = None


def extract_manifest_from_content(content: str) -> dict[str, Any]:
    if not content:
        return {}
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    data: dict[str, Any] = {}
    for line in block.splitlines():
        if ':' not in line:
            continue
        key, raw = line.split(':', 1)
        key = key.strip().lower().replace(' ', '_')
        value = raw.strip()
        if not key or not value:
            continue
        if key in {'permissions', 'capabilities', 'entrypoints', 'tools', 'actions'}:
            data[key] = [part.strip() for part in value.split(',') if part.strip()]
        else:
            data[key] = value
    return data


def validate_plugin_source(content: str) -> list[str]:
    errors: list[str] = []
    if not content or not content.strip():
        return ['Plugin source is empty']
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return [f'Invalid Python syntax: {exc.msg} (line {exc.lineno})']
    banned = {
        'os.system',
        'subprocess.Popen',
        'subprocess.call',
        'subprocess.run',
        'eval',
        'exec',
        '__import__',
        'compile',
        'ctypes',
        'socket.socket',
    }
    for item in banned:
        if item in content:
            errors.append(f'Potentially unsafe construct is not allowed in plugins: {item}')
    has_filter = any(isinstance(node, ast.ClassDef) and node.name == 'Filter' for node in tree.body)
    has_action = any(
        isinstance(node, ast.ClassDef) and node.name in {'Action', 'Tools', 'Pipe'} for node in tree.body
    )
    if not has_filter and not has_action:
        errors.append('Plugin must define a Filter, Action, Tools, or Pipe class')
    return errors


def validate_plugin_manifest(raw: dict[str, Any] | None, content: str = '') -> PluginValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    payload = dict(raw or {})
    extracted = extract_manifest_from_content(content)
    for key, value in extracted.items():
        payload.setdefault(key, value)
    if content:
        errors.extend(validate_plugin_source(content))
    try:
        manifest = PluginManifest.model_validate(payload)
    except Exception as exc:
        return PluginValidationResult(valid=False, errors=[str(exc), *errors], warnings=warnings)
    if not manifest.permissions:
        warnings.append('No permissions declared; plugin will run with no elevated capabilities listed')
    if manifest.type == 'filter' and 'Filter' not in content:
        warnings.append('Manifest type is filter but no Filter class was detected in source')
    if errors:
        return PluginValidationResult(valid=False, errors=errors, warnings=warnings, manifest=manifest)
    return PluginValidationResult(valid=True, errors=[], warnings=warnings, manifest=manifest)


def function_to_plugin_record(function: Any) -> dict[str, Any]:
    meta = getattr(function, 'meta', None)
    if hasattr(meta, 'model_dump'):
        meta = meta.model_dump()
    meta = meta if isinstance(meta, dict) else {}
    manifest_raw = meta.get('manifest') if isinstance(meta.get('manifest'), dict) else {}
    validation = validate_plugin_manifest(
        {
            'id': getattr(function, 'id', '') or manifest_raw.get('id', ''),
            'name': getattr(function, 'name', '') or manifest_raw.get('name', ''),
            'description': meta.get('description') or manifest_raw.get('description', ''),
            **manifest_raw,
            'type': getattr(function, 'type', None) or manifest_raw.get('type', 'filter'),
        },
        content=getattr(function, 'content', '') or '',
    )
    status = 'active' if getattr(function, 'is_active', False) else 'disabled'
    if not validation.valid:
        status = 'invalid'
    return {
        'id': getattr(function, 'id', None),
        'name': getattr(function, 'name', None),
        'description': meta.get('description') or '',
        'version': (validation.manifest.version if validation.manifest else '0.0.0'),
        'author': (validation.manifest.author if validation.manifest else ''),
        'icon': (validation.manifest.icon if validation.manifest else ''),
        'type': getattr(function, 'type', None),
        'capabilities': (validation.manifest.capabilities if validation.manifest else []),
        'permissions': (validation.manifest.permissions if validation.manifest else []),
        'status': status,
        'is_active': bool(getattr(function, 'is_active', False)),
        'is_global': bool(getattr(function, 'is_global', False)),
        'compatibility': (validation.manifest.required_open_webui_version if validation.manifest else ''),
        'validation': {
            'valid': validation.valid,
            'errors': validation.errors,
            'warnings': validation.warnings,
        },
        'updated_at': getattr(function, 'updated_at', None),
        'created_at': getattr(function, 'created_at', None),
    }


PERMISSION_CATALOG = [
    {'id': 'network', 'label': 'Network access', 'description': 'Call external or local network services'},
    {'id': 'chat.read', 'label': 'Read chats', 'description': 'Read chat messages and metadata'},
    {'id': 'chat.write', 'label': 'Write chats', 'description': 'Modify or append chat content'},
    {'id': 'files.read', 'label': 'Read files', 'description': 'Read uploaded or workspace files'},
    {'id': 'files.write', 'label': 'Write files', 'description': 'Create or modify files'},
    {'id': 'tools.execute', 'label': 'Execute tools', 'description': 'Invoke tools during chat'},
    {'id': 'models.access', 'label': 'Model access', 'description': 'Call local or configured models'},
    {'id': 'memory.access', 'label': 'Memory access', 'description': 'Read or write long-term memories'},
]

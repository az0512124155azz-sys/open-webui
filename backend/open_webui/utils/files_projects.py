"""Stage 9 – Smart attachments, file actions, project bundles."""

from __future__ import annotations

import mimetypes
import os
import re
from typing import Any

_CODE_EXT = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.svelte', '.vue', '.go', '.rs', '.java',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.sh', '.bash', '.zsh', '.sql', '.html', '.css', '.scss', '.json', '.yaml',
    '.yml', '.toml', '.xml', '.md', '.txt', '.r', '.m',
}
_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg', '.ico'}
_3D_EXT = {'.obj', '.stl', '.glb', '.gltf', '.fbx', '.ply', '.3mf'}
_DOC_EXT = {'.pdf', '.docx', '.doc', '.odt', '.rtf', '.epub'}
_ARCHIVE_EXT = {'.zip', '.tar', '.gz', '.tgz', '.rar', '.7z'}
_AUDIO_EXT = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}
_VIDEO_EXT = {'.mp4', '.webm', '.mkv', '.avi', '.mov'}


def classify_file(filename: str, content_type: str | None = None) -> dict[str, Any]:
    name = (filename or 'file').split('?')[0]
    ext = os.path.splitext(name)[1].lower()
    mime = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')

    kind = 'binary'
    treatments: list[str] = ['attach', 'download']
    actions: list[str] = ['download', 'send_to_model']

    if ext in _IMAGE_EXT or mime.startswith('image/'):
        kind = 'image'
        treatments += ['preview', 'image_analysis']
        actions += ['preview', 'analyze', 'summarize']
    elif ext in _3D_EXT:
        kind = '3d'
        treatments += ['preview', '3d_treatment']
        actions += ['preview', '3d_export']
    elif ext in _CODE_EXT or mime.startswith('text/'):
        kind = 'source_code' if ext in _CODE_EXT else 'text'
        treatments += ['preview', 'extract', 'parse', 'source_code_treatment']
        actions += ['preview', 'open_as_code', 'extract_text', 'summarize']
    elif ext in _DOC_EXT:
        kind = 'document'
        treatments += ['extract', 'parse', 'index']
        actions += ['extract_text', 'summarize', 'analyze']
    elif ext in _ARCHIVE_EXT:
        kind = 'archive'
        treatments += ['extract']
        actions += ['extract']
    elif ext in _AUDIO_EXT or mime.startswith('audio/'):
        kind = 'audio'
        treatments += ['preview']
        actions += ['preview']
    elif ext in _VIDEO_EXT or mime.startswith('video/'):
        kind = 'video'
        treatments += ['preview']
        actions += ['preview']
    else:
        treatments += ['index']
        actions += ['summarize']

    treatments = list(dict.fromkeys(treatments))
    actions = list(dict.fromkeys(actions))

    return {
        'filename': name,
        'extension': ext,
        'mime': mime,
        'kind': kind,
        'treatments': treatments,
        'actions': actions,
    }


_SAFE_NAME = re.compile(r'[^A-Za-z0-9._\-]+')


def safe_filename(name: str, max_len: int = 180) -> str:
    base = os.path.basename(name or 'file')
    base = _SAFE_NAME.sub('_', base).strip('._') or 'file'
    return base[:max_len]


def project_bundle_schema() -> dict[str, Any]:
    return {
        'fields': [
            'id', 'name', 'description', 'chat_ids', 'file_ids', 'instructions',
            'memory_ids', 'model_ids', 'skill_ids', 'plugin_ids', 'settings',
        ],
        'note': 'Projects group existing Open WebUI resources; not a separate UX silo.',
    }

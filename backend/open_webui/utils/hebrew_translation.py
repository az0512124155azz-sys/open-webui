from __future__ import annotations

import asyncio
import hashlib
import html
import os
import re
from typing import Any, Literal

import aiohttp
from langdetect import DetectorFactory, LangDetectException, detect
from pydantic import BaseModel, Field

DetectorFactory.seed = 0

_HEBREW_RE = re.compile(r'[\u0590-\u05FF]')
_PROTECTED_RE = re.compile(
    r'(```[\s\S]*?```|`[^`\n]+`|https?://[^\s<>()]+|(?:[A-Za-z]:\\|/)[\w .\-/\\]+(?:\.[A-Za-z0-9]{1,8})?)',
    re.MULTILINE,
)
_MAX_CHUNK = 2800


def _message_text(message: dict[str, Any]) -> str | None:
    content = message.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [part.get('text', '') for part in content if isinstance(part, dict) and part.get('type') == 'text']
        return '\n'.join(part for part in parts if part)
    return None


def _set_message_text(message: dict[str, Any], text: str) -> None:
    content = message.get('content')
    if isinstance(content, str) or content is None:
        message['content'] = text
        return
    if isinstance(content, list):
        replaced = False
        for part in content:
            if isinstance(part, dict) and part.get('type') == 'text':
                part['text'] = text if not replaced else ''
                replaced = True
        if not replaced:
            content.append({'type': 'text', 'text': text})


def _mask_protected(text: str) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = f'OWUIX{len(protected):04d}X'
        protected[token] = match.group(0)
        return token

    return _PROTECTED_RE.sub(replace, text), protected


def _restore_protected(text: str, protected: dict[str, str]) -> str:
    for token, value in protected.items():
        text = text.replace(token, value)
    return text


def _split_chunks(text: str, max_chars: int = _MAX_CHUNK) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    current = ''
    for paragraph in re.split(r'(\n{2,})', text):
        if len(current) + len(paragraph) <= max_chars:
            current += paragraph
            continue
        if current:
            chunks.append(current)
            current = ''
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
    if current:
        chunks.append(current)
    return chunks


def _contains_hebrew(text: str) -> bool:
    return bool(_HEBREW_RE.search(text))


def _detect_language(text: str) -> str:
    sample = _PROTECTED_RE.sub(' ', text).strip()
    if not sample:
        return 'unknown'
    if _contains_hebrew(sample):
        return 'he'
    try:
        return detect(sample)
    except LangDetectException:
        return 'unknown'


class UserValves(BaseModel):
    enabled: bool = Field(default=False, description='Enable automatic Hebrew ↔ English translation')
    engine: Literal['libretranslate', 'ollama'] = Field(
        default='libretranslate',
        description='Preferred offline translation engine',
        json_schema_extra={
            'input': {
                'type': 'select',
                'options': [
                    {'value': 'libretranslate', 'label': 'LibreTranslate'},
                    {'value': 'ollama', 'label': 'Ollama model'},
                ],
            }
        },
    )
    libretranslate_url: str = Field(default='http://libretranslate:5000', description='Local LibreTranslate URL')
    ollama_model: str = Field(default='qwen2.5:3b', description='Local Ollama translation model')
    show_original: bool = Field(default=True, description='Show original assistant text in a collapsed section')
    apply_to: Literal['both', 'user', 'assistant'] = Field(
        default='both',
        description='Translate user messages, assistant responses, or both',
        json_schema_extra={
            'input': {
                'type': 'select',
                'options': [
                    {'value': 'both', 'label': 'Both'},
                    {'value': 'user', 'label': 'User messages only'},
                    {'value': 'assistant', 'label': 'Model responses only'},
                ],
            }
        },
    )


class Filter:
    """Offline Hebrew ↔ English translation filter for Open WebUI."""

    def __init__(self):
        self.name = 'Automatic Hebrew Translation'
        self.UserValves = UserValves
        self._language_cache: dict[str, str] = {}

    def _settings(self, __user__: dict | None) -> UserValves:
        if not __user__:
            return UserValves()
        valves = __user__.get('valves')
        return valves if isinstance(valves, UserValves) else UserValves(**(valves or {}))

    def _cached_language(self, text: str, message_id: str | None = None) -> str:
        key = message_id or hashlib.sha1(text.encode('utf-8')).hexdigest()
        if key not in self._language_cache:
            if len(self._language_cache) > 2048:
                self._language_cache.clear()
            self._language_cache[key] = _detect_language(text)
        return self._language_cache[key]

    async def _translate_libre(self, text: str, source: str, target: str, url: str) -> str:
        endpoint = f'{url.rstrip("/")}/translate'
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.post(
                endpoint,
                json={'q': text, 'source': source, 'target': target, 'format': 'text'},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                translated = data.get('translatedText')
                if not isinstance(translated, str):
                    raise RuntimeError('LibreTranslate returned no translatedText')
                return translated

    async def _translate_ollama(self, text: str, source: str, target: str, model: str) -> str:
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434').split(';')[0].rstrip('/')
        source_name = 'Hebrew' if source == 'he' else 'English'
        target_name = 'Hebrew' if target == 'he' else 'English'
        prompt = (
            f'Translate the following {source_name} text to {target_name}. '
            'Return only the translation. Preserve Markdown markers, placeholders such as OWUIX0000X, emojis, and numbers exactly.\n\n'
            f'{text}'
        )
        timeout = aiohttp.ClientTimeout(total=90)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.post(
                f'{base_url}/api/generate',
                json={'model': model, 'prompt': prompt, 'stream': False, 'keep_alive': -1},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                translated = data.get('response')
                if not isinstance(translated, str):
                    raise RuntimeError('Ollama returned no response')
                return translated.strip()

    async def _translate_chunk(self, text: str, source: str, target: str, settings: UserValves) -> str:
        if not text.strip():
            return text
        masked, protected = _mask_protected(text)
        if not masked.strip():
            return text

        async def libre() -> str:
            return await self._translate_libre(masked, source, target, settings.libretranslate_url)

        async def ollama() -> str:
            return await self._translate_ollama(masked, source, target, settings.ollama_model)

        try:
            translated = await (libre() if settings.engine == 'libretranslate' else ollama())
        except Exception:
            # Offline local fallback in either direction: if the preferred engine
            # is unavailable, try the other configured local engine.
            translated = await (ollama() if settings.engine == 'libretranslate' else libre())
        return _restore_protected(translated, protected)

    async def _translate_text(self, text: str, source: str, target: str, settings: UserValves) -> str:
        chunks = _split_chunks(text)
        translated = await asyncio.gather(*(self._translate_chunk(chunk, source, target, settings) for chunk in chunks))
        return ''.join(translated)

    async def inlet(self, body: dict, __user__: dict | None = None) -> dict:
        settings = self._settings(__user__)
        if not settings.enabled or settings.apply_to not in {'both', 'user'}:
            return body

        messages = body.get('messages') or []
        message = next((item for item in reversed(messages) if item.get('role') == 'user'), None)
        if not message:
            return body
        original = _message_text(message)
        if not original:
            return body

        message_id = str(message.get('id') or body.get('metadata', {}).get('message_id') or '') or None
        if self._cached_language(original, message_id) != 'he':
            return body

        translated = await self._translate_text(original, 'he', 'en', settings)
        message.setdefault('metadata', {})['translation_original'] = original
        message['metadata']['translation_source_language'] = 'he'
        _set_message_text(message, translated)
        return body

    async def outlet(self, body: dict, __user__: dict | None = None) -> dict:
        settings = self._settings(__user__)
        if not settings.enabled or settings.apply_to not in {'both', 'assistant'}:
            return body

        messages = body.get('messages') or []
        message = next((item for item in reversed(messages) if item.get('role') == 'assistant'), None)
        if message is None and body.get('message', {}).get('role') == 'assistant':
            message = body['message']
        if not message:
            return body

        original = _message_text(message)
        if not original:
            return body
        message_id = str(message.get('id') or body.get('metadata', {}).get('message_id') or '') or None
        language = self._cached_language(original, message_id)
        if language not in {'en', 'unknown'} or _contains_hebrew(original):
            return body

        translated = await self._translate_text(original, 'en', 'he', settings)
        message.setdefault('metadata', {})['translation_original'] = original
        message['metadata']['translation_source_language'] = 'en'
        if settings.show_original:
            safe_original = html.escape(original, quote=False)
            translated = f'{translated}\n\n<details><summary>Show original</summary>\n\n{safe_original}\n\n</details>'
        _set_message_text(message, translated)
        return body

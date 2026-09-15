"""seed built-in Hebrew translation filter

Revision ID: c0f1a2b3c4d5
Revises: d4c1a8e37b62
Create Date: 2026-09-15 13:55:00

"""

from collections.abc import Sequence
import time

import sqlalchemy as sa
from alembic import op

revision: str = 'c0f1a2b3c4d5'
down_revision: str | None = 'd4c1a8e37b62'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FUNCTION_ID = 'automatic_hebrew_translation'
_FUNCTION_SOURCE = '''"""
title: Automatic Hebrew Translation
description: Offline Hebrew ↔ English translation filter using LibreTranslate with local Ollama fallback.
version: 1.0.0
"""
from open_webui.utils.hebrew_translation import Filter
'''


def upgrade() -> None:
    function = sa.table(
        'function',
        sa.column('id', sa.String),
        sa.column('user_id', sa.String),
        sa.column('name', sa.Text),
        sa.column('type', sa.Text),
        sa.column('content', sa.Text),
        sa.column('meta', sa.JSON),
        sa.column('valves', sa.JSON),
        sa.column('is_active', sa.Boolean),
        sa.column('is_global', sa.Boolean),
        sa.column('updated_at', sa.BigInteger),
        sa.column('created_at', sa.BigInteger),
    )
    connection = op.get_bind()
    exists = connection.execute(sa.select(function.c.id).where(function.c.id == _FUNCTION_ID)).first()
    if exists:
        return

    now = int(time.time())
    connection.execute(
        function.insert().values(
            id=_FUNCTION_ID,
            user_id='system',
            name='Automatic Hebrew Translation',
            type='filter',
            content=_FUNCTION_SOURCE,
            meta={
                'description': (
                    'Translates Hebrew prompts to English before inference and English model responses '
                    'back to Hebrew using local translation services only.'
                ),
                'manifest': {
                    'title': 'Automatic Hebrew Translation',
                    'description': 'Offline Hebrew ↔ English translation filter',
                    'version': '1.0.0',
                },
            },
            valves=None,
            is_active=True,
            is_global=True,
            updated_at=now,
            created_at=now,
        )
    )


def downgrade() -> None:
    function = sa.table(
        'function',
        sa.column('id', sa.String),
        sa.column('user_id', sa.String),
    )
    # Only remove the first-party seeded row; preserve a user-owned replacement.
    op.get_bind().execute(function.delete().where(function.c.id == _FUNCTION_ID).where(function.c.user_id == 'system'))

"""add source_chat_id to memory

Revision ID: c0f1a2b3c4d6
Revises: c0f1a2b3c4d5
Create Date: 2026-09-15 14:10:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c0f1a2b3c4d6'
down_revision: str | None = 'c0f1a2b3c4d5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('memory', sa.Column('source_chat_id', sa.String(), nullable=True))
    op.create_index('ix_memory_source_chat_id', 'memory', ['source_chat_id'])

    # Existing recent builds already recorded chat_id in memory.meta. Backfill
    # without relying on database-specific JSON operators.
    memory = sa.table(
        'memory',
        sa.column('id', sa.String),
        sa.column('meta', sa.JSON),
        sa.column('source_chat_id', sa.String),
    )
    connection = op.get_bind()
    for memory_id, meta in connection.execute(sa.select(memory.c.id, memory.c.meta)).all():
        if isinstance(meta, dict) and meta.get('chat_id'):
            connection.execute(memory.update().where(memory.c.id == memory_id).values(source_chat_id=str(meta['chat_id'])))


def downgrade() -> None:
    op.drop_index('ix_memory_source_chat_id', table_name='memory')
    op.drop_column('memory', 'source_chat_id')

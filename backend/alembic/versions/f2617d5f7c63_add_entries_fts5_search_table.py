"""add entries fts5 search table

Revision ID: f2617d5f7c63
Revises: c15bab78e938
Create Date: 2026-08-22 21:19:39.586754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.core.search import FTS_SETUP_SQL, FTS_TEARDOWN_SQL


# revision identifiers, used by Alembic.
revision: str = 'f2617d5f7c63'
down_revision: Union[str, Sequence[str], None] = 'c15bab78e938'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    for statement in FTS_SETUP_SQL:
        # alembic's escape hatch for running raw SQL
        op.execute(statement)


def downgrade() -> None:
    """Downgrade schema."""
    for statement in FTS_TEARDOWN_SQL:
        op.execute(statement)

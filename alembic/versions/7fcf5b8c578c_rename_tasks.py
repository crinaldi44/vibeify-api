"""rename tasks

Revision ID: 7fcf5b8c578c
Revises: 26aae22c66ed
Create Date: 2026-01-22 13:06:40.090300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fcf5b8c578c'
down_revision: Union[str, None] = '26aae22c66ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('tasks', 'review_items')


def downgrade() -> None:
    op.rename_table('review_items', 'tasks')

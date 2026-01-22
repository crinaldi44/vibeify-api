"""initial_role

Revision ID: 2ec025f18963
Revises: 072923716b5c
Create Date: 2026-01-22 09:36:44.708272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ec025f18963'
down_revision: Union[str, None] = '072923716b5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_active', sa.Boolean)
    )
    op.bulk_insert(roles_table, [
        {'id': 1, 'name': 'Administrator', 'description': 'Full access', 'is_active': True},
        {'id': 2, 'name': 'User', 'description': 'Standard user', 'is_active': True},
    ])


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE id IN (1, 2)")

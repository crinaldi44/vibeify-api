"""task model field

Revision ID: 26aae22c66ed
Revises: 2ec025f18963
Create Date: 2026-01-22 13:03:40.984078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26aae22c66ed'
down_revision: Union[str, None] = '2ec025f18963'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

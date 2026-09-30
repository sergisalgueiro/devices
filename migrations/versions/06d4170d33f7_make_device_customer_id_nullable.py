"""make_device_customer_id_nullable

Revision ID: 06d4170d33f7
Revises: f1e2d3c4b5a6
Create Date: 2026-09-25 11:58:37.902146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06d4170d33f7'
down_revision: Union[str, Sequence[str], None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('devices', 'customer_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    raise NotImplementedError(
        "Downgrades are prohibited by engineering policy. "
    )

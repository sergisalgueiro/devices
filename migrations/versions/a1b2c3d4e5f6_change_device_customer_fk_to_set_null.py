"""change_device_customer_fk_to_set_null

Revision ID: a1b2c3d4e5f6
Revises: 06d4170d33f7
Create Date: 2026-09-28 09:23:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '06d4170d33f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change devices.customer_id FK from RESTRICT to SET NULL.

    Allows deleting a customer while they still own devices. The FK will
    automatically null out customer_id on all owned devices, orphaning them
    back to the unassigned pool rather than blocking the delete.
    """
    # Drop the existing RESTRICT constraint and recreate with SET NULL.
    op.drop_constraint('fk_devices_customer_id_customers', 'devices', type_='foreignkey')
    op.create_foreign_key(
        'fk_devices_customer_id_customers',
        'devices', 'customers',
        ['customer_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    raise NotImplementedError(
        "Downgrades are prohibited by engineering policy. "
    )

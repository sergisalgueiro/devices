"""add_customer_indexes

Revision ID: f1e2d3c4b5a6
Revises: 9023476ba729
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, Sequence[str], None] = '9023476ba729'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_customers_created_at_id', 'customers', ['created_at', 'id'])
    op.create_index('ix_customers_name_id', 'customers', ['name', 'id'])
    op.create_index('ix_customers_email_id', 'customers', ['email', 'id'])
    op.create_index('ix_customers_country', 'customers', ['country'])
    op.create_index('ix_customers_language', 'customers', ['language'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_customers_language', table_name='customers')
    op.drop_index('ix_customers_country', table_name='customers')
    op.drop_index('ix_customers_email_id', table_name='customers')
    op.drop_index('ix_customers_name_id', table_name='customers')
    op.drop_index('ix_customers_created_at_id', table_name='customers')

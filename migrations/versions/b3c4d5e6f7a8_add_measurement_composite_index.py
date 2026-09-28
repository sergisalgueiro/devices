"""add_measurement_composite_index

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-09-28 00:00:00.000000

Replace the single-column ix_measurements_device_id index with a composite
(device_id, timestamp, id) index.  The composite index subsumes the original
and serves the canonical list query:

    WHERE device_id = :id  ORDER BY timestamp, id

without a filesort.  The id column acts as a deterministic tiebreaker for
cursor-based pagination when multiple rows share the same timestamp.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The original index was created by SQLAlchemy's index=True shorthand.
    op.drop_index("ix_measurements_device_id", table_name="measurements")
    op.create_index(
        "ix_measurements_device_id_timestamp_id",
        "measurements",
        ["device_id", "timestamp", "id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_measurements_device_id_timestamp_id", table_name="measurements")
    op.create_index("ix_measurements_device_id", "measurements", ["device_id"])

"""Add optional plot matching details.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("land_plots") as batch_op:
        batch_op.add_column(sa.Column("area", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("land_use", sa.String(length=256), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("land_plots") as batch_op:
        batch_op.drop_column("land_use")
        batch_op.drop_column("area")

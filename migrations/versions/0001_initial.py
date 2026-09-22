"""Initial bot schema.

Revision ID: 0001
Revises:
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("telegram_id", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)
    op.create_table("land_plots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("cadastral_number", sa.String(64)), sa.Column("region", sa.String(128), nullable=False), sa.Column("municipality", sa.String(128), nullable=False), sa.Column("submitted_at", sa.Date(), nullable=False), sa.Column("authority", sa.String(256)), sa.Column("address", sa.String(256)), sa.Column("comment", sa.Text()), sa.Column("status", sa.String(32), nullable=False), sa.Column("tracking_enabled", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_land_plots_user_id", "land_plots", ["user_id"])
    op.create_table("notices", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("plot_id", sa.Integer(), sa.ForeignKey("land_plots.id"), nullable=False, unique=True), sa.Column("source_url", sa.String(1024)), sa.Column("published_at", sa.Date()), sa.Column("deadline", sa.Date(), nullable=False), sa.Column("comment", sa.Text()))
    op.create_table("auctions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("plot_id", sa.Integer(), sa.ForeignKey("land_plots.id"), nullable=False, unique=True), sa.Column("source_url", sa.String(1024)), sa.Column("application_deadline", sa.Date()), sa.Column("auction_date", sa.Date()), sa.Column("comment", sa.Text()))
    op.create_table("sent_reminders", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("plot_id", sa.Integer(), sa.ForeignKey("land_plots.id"), nullable=False), sa.Column("kind", sa.String(64), nullable=False), sa.Column("due_date", sa.Date(), nullable=False), sa.Column("sent_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("plot_id", "kind", "due_date", name="uq_reminder"))
    op.create_index("ix_sent_reminders_plot_id", "sent_reminders", ["plot_id"])


def downgrade() -> None:
    op.drop_table("sent_reminders")
    op.drop_table("auctions")
    op.drop_table("notices")
    op.drop_table("land_plots")
    op.drop_table("users")

"""fx and oauth columns

Revision ID: 0004_fx_oauth
Revises: 0003_notifications
Create Date: 2026-02-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_fx_oauth"
down_revision = "0003_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("oauth_provider", sa.String(length=30), nullable=True))
    op.add_column("users", sa.Column("oauth_subject", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_users_oauth_provider_subject",
        "users",
        ["oauth_provider", "oauth_subject"],
        unique=False,
    )

    op.add_column("contributions", sa.Column("charged_usd_cents", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("contributions", "charged_usd_cents")
    op.drop_index("ix_users_oauth_provider_subject", table_name="users")
    op.drop_column("users", "oauth_subject")
    op.drop_column("users", "oauth_provider")

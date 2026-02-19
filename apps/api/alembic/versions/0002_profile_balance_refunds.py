"""profile, balances, refunds

Revision ID: 0002_profile_balance_refunds
Revises: 0001_init
Create Date: 2026-02-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_profile_balance_refunds"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("nickname", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("theme", sa.String(length=10), nullable=False, server_default="light"))
    op.add_column("users", sa.Column("balance_cents", sa.Integer(), nullable=False, server_default="100000"))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "viewer_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("viewer_token_hash", sa.String(length=64), nullable=False),
        sa.Column("balance_cents", sa.Integer(), nullable=False, server_default="100000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_viewer_accounts_hash", "viewer_accounts", ["viewer_token_hash"], unique=True)

    op.add_column(
        "contributions",
        sa.Column("contributor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("contributions", sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_contributions_user", "contributions", ["contributor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_contributions_user", table_name="contributions")
    op.drop_column("contributions", "refunded_at")
    op.drop_column("contributions", "contributor_user_id")

    op.drop_index("ix_viewer_accounts_hash", table_name="viewer_accounts")
    op.drop_table("viewer_accounts")

    op.drop_column("users", "email_verified")
    op.drop_column("users", "balance_cents")
    op.drop_column("users", "theme")
    op.drop_column("users", "birth_date")
    op.drop_column("users", "bio")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "nickname")

"""centralize authentication in identity-service

Revision ID: 004_centralize_identity
Revises: 003_remove_playback_sync
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa


revision = "004_centralize_identity"
down_revision = "003_remove_playback_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable permits a safe rollout: existing profiles are bound on their first
    # valid identity-service login (by verified email), retaining all FKs.
    op.add_column("users", sa.Column("identity_user_id", sa.String(length=36), nullable=True))
    op.create_index("ix_users_identity_user_id", "users", ["identity_user_id"], unique=True)
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=True)
    op.drop_column("users", "hashed_password")


def downgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=False)
    op.drop_index("ix_users_identity_user_id", table_name="users")
    op.drop_column("users", "identity_user_id")

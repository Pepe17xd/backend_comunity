"""remove playback synchronization schema

Revision ID: 003_remove_playback_sync
Revises: 002_create_watch_rooms
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa


revision = "003_remove_playback_sync"
down_revision = "002_create_watch_rooms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("playback_states")


def downgrade() -> None:
    op.create_table(
        "playback_states",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("watch_room_id", sa.String(36), nullable=False),
        sa.Column("position_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", sa.Enum("PLAYING", "PAUSED", name="playbackstatus"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["watch_room_id"], ["watch_rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watch_room_id", name="uq_playback_state_room"),
    )

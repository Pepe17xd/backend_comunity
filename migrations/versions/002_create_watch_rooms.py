"""create watch rooms

Revision ID: 002_create_watch_rooms
Revises: 001_initial
Create Date: 2026-09-05
"""
from alembic import op
import sqlalchemy as sa

revision = "002_create_watch_rooms"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("watch_rooms", sa.Column("id", sa.String(36), nullable=False), sa.Column("code", sa.String(32), nullable=False), sa.Column("club_id", sa.Integer(), nullable=True), sa.Column("host_user_id", sa.Integer(), nullable=False), sa.Column("movie_id", sa.String(36), nullable=False), sa.Column("status", sa.Enum("WAITING", "PLAYING", "PAUSED", "FINISHED", name="watchroomstatus"), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]), sa.ForeignKeyConstraint(["host_user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code", name="uq_watch_rooms_code"))
    op.create_index("ix_watch_rooms_club_id", "watch_rooms", ["club_id"])
    op.create_index("ix_watch_rooms_host_user_id", "watch_rooms", ["host_user_id"])
    op.create_index("ix_watch_rooms_movie_id", "watch_rooms", ["movie_id"])
    op.create_table("watch_participants", sa.Column("id", sa.String(36), nullable=False), sa.Column("watch_room_id", sa.String(36), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("nickname", sa.String(100), nullable=False), sa.Column("role", sa.Enum("HOST", "VIEWER", name="watchparticipantrole"), nullable=False), sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.ForeignKeyConstraint(["watch_room_id"], ["watch_rooms.id"]), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("watch_room_id", "user_id", name="uq_watch_participant_room_user"))
    op.create_index("ix_watch_participants_watch_room_id", "watch_participants", ["watch_room_id"])
    op.create_index("ix_watch_participants_user_id", "watch_participants", ["user_id"])
    op.create_table("playback_states", sa.Column("id", sa.String(36), nullable=False), sa.Column("watch_room_id", sa.String(36), nullable=False), sa.Column("position_seconds", sa.Integer(), nullable=False, server_default="0"), sa.Column("state", sa.Enum("PLAYING", "PAUSED", name="playbackstatus"), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.ForeignKeyConstraint(["watch_room_id"], ["watch_rooms.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("watch_room_id", name="uq_playback_state_room"))


def downgrade() -> None:
    op.drop_table("playback_states")
    op.drop_index("ix_watch_participants_user_id", table_name="watch_participants")
    op.drop_index("ix_watch_participants_watch_room_id", table_name="watch_participants")
    op.drop_table("watch_participants")
    op.drop_index("ix_watch_rooms_movie_id", table_name="watch_rooms")
    op.drop_index("ix_watch_rooms_host_user_id", table_name="watch_rooms")
    op.drop_index("ix_watch_rooms_club_id", table_name="watch_rooms")
    op.drop_table("watch_rooms")

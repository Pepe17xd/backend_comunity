import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class WatchRoomStatus(str, enum.Enum):
    WAITING = "WAITING"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class WatchParticipantRole(str, enum.Enum):
    HOST = "HOST"
    VIEWER = "VIEWER"


class WatchRoom(Base):
    __tablename__ = "watch_rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True, index=True)
    host_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    movie_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[WatchRoomStatus] = mapped_column(
        Enum(WatchRoomStatus), default=WatchRoomStatus.WAITING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    participants = relationship("WatchParticipant", back_populates="watch_room", cascade="all, delete-orphan")


class WatchParticipant(Base):
    __tablename__ = "watch_participants"
    __table_args__ = (UniqueConstraint("watch_room_id", "user_id", name="uq_watch_participant_room_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    watch_room_id: Mapped[str] = mapped_column(ForeignKey("watch_rooms.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[WatchParticipantRole] = mapped_column(
        Enum(WatchParticipantRole), default=WatchParticipantRole.VIEWER, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    watch_room = relationship("WatchRoom", back_populates="participants")

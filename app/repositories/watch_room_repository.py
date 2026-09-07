from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.watch_room import WatchParticipant, WatchRoom


class WatchRoomRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, entity):
        self.db.add(entity)
        self.db.flush()
        return entity

    def get_by_code(self, code: str) -> WatchRoom | None:
        stmt = select(WatchRoom).where(WatchRoom.code == code).options(selectinload(WatchRoom.participants))
        return self.db.scalar(stmt)

    def get_by_id(self, room_id: str) -> WatchRoom | None:
        return self.db.get(WatchRoom, room_id)

    def get_participant(self, room_id: str, user_id: int) -> WatchParticipant | None:
        return self.db.scalar(select(WatchParticipant).where(WatchParticipant.watch_room_id == room_id, WatchParticipant.user_id == user_id))

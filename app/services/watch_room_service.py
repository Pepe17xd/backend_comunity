import secrets
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.user import User
from app.models.watch_room import WatchParticipant, WatchParticipantRole, WatchRoom
from app.repositories.watch_room_repository import WatchRoomRepository
from app.schemas.watch_room import WatchRoomCreate, WatchRoomJoin


class WatchRoomService:
    def __init__(self, db: Session):
        self.db = db
        self.rooms = WatchRoomRepository(db)

    def _code(self) -> str:
        # Cryptographically random invite code; the unique DB constraint remains the final guard.
        while True:
            code = f"ASTRA-{secrets.randbelow(10000):04d}"
            if not self.rooms.get_by_code(code):
                return code

    def create_room(self, payload: WatchRoomCreate) -> WatchRoom:
        host = self.db.get(User, payload.host_user_id)
        if not host:
            raise HTTPException(404, "Usuario anfitrión no encontrado")
        if payload.club_id is not None and not self.db.get(Club, payload.club_id):
            raise HTTPException(404, "Club no encontrado")
        room = WatchRoom(code=self._code(), movie_id=str(payload.movie_id), club_id=payload.club_id, host_user_id=payload.host_user_id)
        self.rooms.add(room)
        self.rooms.add(WatchParticipant(
            watch_room_id=room.id,
            user_id=payload.host_user_id,
            nickname=host.display_name or host.username,
            role=WatchParticipantRole.HOST,
        ))
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_room(self, code: str) -> WatchRoom:
        room = self.rooms.get_by_code(code.upper())
        if not room:
            raise HTTPException(404, "Sala no encontrada")
        return room

    def join_room(self, code: str, payload: WatchRoomJoin) -> WatchRoom:
        room = self.get_room(code)
        if not self.db.get(User, payload.user_id):
            raise HTTPException(404, "Usuario no encontrado")
        if self.rooms.get_participant(room.id, payload.user_id):
            raise HTTPException(409, "El usuario ya participa en esta sala")
        self.rooms.add(WatchParticipant(watch_room_id=room.id, user_id=payload.user_id, nickname=payload.nickname, role=WatchParticipantRole.VIEWER))
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(409, "El usuario ya participa en esta sala") from exc
        return room

    def leave_room(self, code: str, user_id: int) -> None:
        room = self.get_room(code)
        participant = self.rooms.get_participant(room.id, user_id)
        if not participant:
            raise HTTPException(404, "Participante no encontrado")
        if participant.role == WatchParticipantRole.HOST:
            raise HTTPException(409, "El anfitrión no puede salir de su propia sala")
        self.db.delete(participant)
        self.db.commit()

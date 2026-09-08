import secrets

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.membership import MembershipRole
from app.models.user import User
from app.models.watch_room import WatchParticipant, WatchParticipantRole, WatchRoom
from app.repositories.membership_repository import MembershipRepository
from app.repositories.watch_room_repository import WatchRoomRepository
from app.schemas.watch_room import WatchRoomCreate, WatchRoomJoin


class WatchRoomService:
    def __init__(self, db: Session):
        self.db = db
        self.rooms = WatchRoomRepository(db)
        self.memberships = MembershipRepository(db)

    def _code(self) -> str:
        while True:
            code = f"ASTRA-{secrets.randbelow(10000):04d}"
            if not self.rooms.get_by_code(code):
                return code

    def create_room(self, payload: WatchRoomCreate, host: User) -> WatchRoom:
        if payload.club_id is not None:
            club = self.db.get(Club, payload.club_id)
            if not club or not club.is_active:
                raise HTTPException(404, "Club no encontrado")
            if not self.memberships.get_by_user_club(host.id, payload.club_id):
                raise HTTPException(403, "Debes pertenecer al club para crear una sala")
        room = WatchRoom(code=self._code(), movie_id=str(payload.movie_id), club_id=payload.club_id, host_user_id=host.id)
        self.rooms.add(room)
        self.rooms.add(WatchParticipant(
            watch_room_id=room.id, user_id=host.id,
            nickname=host.display_name or host.username, role=WatchParticipantRole.HOST,
        ))
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_room(self, code: str) -> WatchRoom:
        room = self.rooms.get_by_code(code.upper())
        if not room:
            raise HTTPException(404, "Sala no encontrada")
        return room

    def join_room(self, code: str, payload: WatchRoomJoin, user: User) -> WatchRoom:
        room = self.get_room(code)
        if room.club_id and not self.memberships.get_by_user_club(user.id, room.club_id):
            raise HTTPException(403, "Debes pertenecer al club para unirte a esta sala")
        if self.rooms.get_participant(room.id, user.id):
            raise HTTPException(409, "El usuario ya participa en esta sala")
        self.rooms.add(WatchParticipant(
            watch_room_id=room.id, user_id=user.id, nickname=payload.nickname,
            role=WatchParticipantRole.VIEWER,
        ))
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(409, "El usuario ya participa en esta sala") from exc
        return room

    def leave_room(self, code: str, user_id: int, actor: User) -> None:
        room = self.get_room(code)
        participant = self.rooms.get_participant(room.id, user_id)
        if not participant:
            raise HTTPException(404, "Participante no encontrado")
        permitted = actor.id == user_id or actor.id == room.host_user_id
        if room.club_id and not permitted:
            membership = self.memberships.get_by_user_club(actor.id, room.club_id)
            permitted = bool(membership and membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN})
        if not permitted:
            raise HTTPException(403, "Permisos insuficientes")
        if participant.role == WatchParticipantRole.HOST:
            raise HTTPException(409, "El anfitrión no puede salir de su propia sala")
        self.db.delete(participant)
        self.db.commit()

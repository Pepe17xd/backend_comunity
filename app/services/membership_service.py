from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.club import ClubVisibility
from app.models.membership import Membership, MembershipRole
from app.repositories.club_repository import ClubRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.user_repository import UserRepository


class MembershipService:
    def __init__(self, db: Session):
        self.db = db
        self.memberships = MembershipRepository(db)
        self.users = UserRepository(db)
        self.clubs = ClubRepository(db)

    def join_club(self, club_id: int, user_id: int) -> Membership:
        club = self.clubs.get(club_id)
        if not club or not club.is_active:
            raise HTTPException(status_code=404, detail="Club no encontrado")

        if club.visibility == ClubVisibility.PRIVATE:
            raise HTTPException(
                status_code=403,
                detail="El club es privado; se requiere flujo de invitación/solicitud",
            )

        if self.memberships.get_by_user_club(user_id, club_id):
            raise HTTPException(status_code=409, detail="El usuario ya pertenece al club")

        membership = Membership(
            user_id=user_id,
            club_id=club_id,
            role=MembershipRole.MEMBER,
        )
        self.memberships.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def list_club_members(self, club_id: int) -> list[Membership]:
        club = self.clubs.get(club_id)
        if not club:
            raise HTTPException(status_code=404, detail="Club no encontrado")
        return self.memberships.list_by_club(club_id)

    def list_user_memberships(self, user_id: int) -> list[Membership]:
        if not self.users.get(user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return self.memberships.list_by_user(user_id)

    def require_role(
        self,
        club_id: int,
        user_id: int,
        allowed_roles: set[MembershipRole],
    ) -> Membership:
        membership = self.memberships.get_by_user_club(user_id, club_id)
        if not membership or membership.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permisos insuficientes")
        return membership

    def change_role(
        self,
        club_id: int,
        user_id: int,
        new_role: MembershipRole,
    ) -> Membership:
        membership = self.memberships.get_by_user_club(user_id, club_id)
        if not membership:
            raise HTTPException(status_code=404, detail="Membresía no encontrada")
        if membership.role == MembershipRole.OWNER:
            raise HTTPException(status_code=400, detail="No se puede cambiar el rol del OWNER")
        if new_role == MembershipRole.OWNER:
            raise HTTPException(
                status_code=400,
                detail="La transferencia de propiedad no está implementada",
            )

        membership.role = new_role
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def leave_club(self, club_id: int, user_id: int) -> None:
        membership = self.memberships.get_by_user_club(user_id, club_id)
        if not membership:
            raise HTTPException(status_code=404, detail="Membresía no encontrada")
        if membership.role == MembershipRole.OWNER:
            raise HTTPException(
                status_code=400,
                detail="El OWNER no puede salir del club sin transferir/eliminar el club",
            )

        self.db.delete(membership)
        self.db.commit()

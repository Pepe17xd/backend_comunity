from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.membership import Membership, MembershipRole
from app.repositories.club_repository import ClubRepository
from app.repositories.membership_repository import MembershipRepository
from app.schemas.club import ClubCreate, ClubUpdate


class ClubService:
    def __init__(self, db: Session):
        self.db = db
        self.clubs = ClubRepository(db)
        self.memberships = MembershipRepository(db)

    def create_club(self, payload: ClubCreate, owner_id: int) -> Club:
        if self.clubs.get_by_name(payload.name):
            raise HTTPException(status_code=409, detail="Ya existe un club con ese nombre")

        club = Club(
            name=payload.name,
            description=payload.description,
            visibility=payload.visibility,
            owner_id=owner_id,
        )
        self.clubs.add(club)

        self.memberships.add(
            Membership(
                user_id=owner_id,
                club_id=club.id,
                role=MembershipRole.OWNER,
            )
        )

        self.db.commit()
        self.db.refresh(club)
        return club

    def get_club(self, club_id: int) -> Club | None:
        return self.clubs.get(club_id)

    def list_clubs(self, skip: int = 0, limit: int = 50) -> list[Club]:
        return self.clubs.list(skip=skip, limit=limit)

    def update_club(self, club_id: int, payload: ClubUpdate) -> Club:
        club = self.clubs.get(club_id)
        if not club or not club.is_active:
            raise HTTPException(status_code=404, detail="Club no encontrado")

        changes = payload.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] != club.name:
            existing = self.clubs.get_by_name(changes["name"])
            if existing:
                raise HTTPException(status_code=409, detail="Ya existe un club con ese nombre")

        for field, value in changes.items():
            setattr(club, field, value)

        self.db.commit()
        self.db.refresh(club)
        return club

    def deactivate_club(self, club_id: int) -> None:
        club = self.clubs.get(club_id)
        if not club:
            raise HTTPException(status_code=404, detail="Club no encontrado")
        club.is_active = False
        self.db.commit()

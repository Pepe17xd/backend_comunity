from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership


class MembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_club(self, user_id: int, club_id: int) -> Membership | None:
        stmt = select(Membership).where(
            Membership.user_id == user_id,
            Membership.club_id == club_id,
        )
        return self.db.scalar(stmt)

    def list_by_club(self, club_id: int) -> list[Membership]:
        stmt = select(Membership).where(Membership.club_id == club_id).order_by(Membership.id)
        return list(self.db.scalars(stmt).all())

    def list_by_user(self, user_id: int) -> list[Membership]:
        stmt = select(Membership).where(Membership.user_id == user_id).order_by(Membership.id)
        return list(self.db.scalars(stmt).all())

    def add(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.flush()
        self.db.refresh(membership)
        return membership

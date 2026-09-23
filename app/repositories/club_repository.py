from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.club import Club


class ClubRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, club_id: int) -> Club | None:
        return self.db.get(Club, club_id)

    def get_by_name(self, name: str) -> Club | None:
        return self.db.scalar(select(Club).where(Club.name == name))

    def list(self, skip: int = 0, limit: int = 50, search: str | None = None) -> list[Club]:
        stmt = select(Club).where(Club.is_active.is_(True))
        if search:
            stmt = stmt.where(Club.name.ilike(f"%{search}%"))
        stmt = stmt.offset(skip).limit(limit).order_by(Club.id)
        return list(self.db.scalars(stmt).all())

    def count(self, search: str | None = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Club.id)).where(Club.is_active.is_(True))
        if search:
            stmt = stmt.where(Club.name.ilike(f"%{search}%"))
        return self.db.scalar(stmt) or 0

    def add(self, club: Club) -> Club:
        self.db.add(club)
        self.db.flush()
        self.db.refresh(club)
        return club

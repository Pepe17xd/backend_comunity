import re

# 1. Add count and search to ClubRepository
with open("backend_comunity/app/repositories/club_repository.py", "r") as f:
    repo = f.read()

repo_find = """    def list(self, skip: int = 0, limit: int = 50) -> list[Club]:
        stmt = (
            select(Club)
            .where(Club.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Club.id)
        )
        return list(self.db.scalars(stmt).all())"""

repo_replace = """    def list(self, skip: int = 0, limit: int = 50, search: str | None = None) -> list[Club]:
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
        return self.db.scalar(stmt) or 0"""

repo = repo.replace(repo_find, repo_replace)
with open("backend_comunity/app/repositories/club_repository.py", "w") as f:
    f.write(repo)

# 2. Add PaginatedClubs to schemas/club.py
with open("backend_comunity/app/schemas/club.py", "a") as f:
    f.write("\n\nclass PaginatedClubs(BaseModel):\n    items: list[ClubRead]\n    total: int\n    page: int\n    size: int\n    pages: int\n")

# 3. Update ClubService
with open("backend_comunity/app/services/club_service.py", "r") as f:
    svc = f.read()

svc_find = """    def list_clubs(self, skip: int = 0, limit: int = 50) -> list[Club]:
        return self.clubs.list(skip=skip, limit=limit)"""

svc_replace = """    def list_clubs(self, skip: int = 0, limit: int = 50, search: str | None = None) -> dict:
        items = self.clubs.list(skip=skip, limit=limit, search=search)
        total = self.clubs.count(search=search)
        page = (skip // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1
        return {"items": items, "total": total, "page": page, "size": limit, "pages": pages}"""

svc = svc.replace(svc_find, svc_replace)
with open("backend_comunity/app/services/club_service.py", "w") as f:
    f.write(svc)

# 4. Update router
with open("backend_comunity/app/api/routes/clubs.py", "r") as f:
    router = f.read()

router = router.replace("from app.schemas.club import ClubCreate, ClubRead, ClubUpdate", "from app.schemas.club import ClubCreate, ClubRead, ClubUpdate, PaginatedClubs")

router_find = """@router.get("", response_model=list[ClubRead])
def list_clubs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ClubService(db).list_clubs(skip=skip, limit=limit)"""

router_replace = """@router.get("", response_model=PaginatedClubs)
def list_clubs(
    search: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    return ClubService(db).list_clubs(skip=skip, limit=size, search=search)"""

router = router.replace(router_find, router_replace)
with open("backend_comunity/app/api/routes/clubs.py", "w") as f:
    f.write(router)

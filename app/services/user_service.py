from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def create_user(self, payload: UserCreate) -> User:
        if self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=409, detail="El email ya está registrado")
        if self.repo.get_by_username(payload.username):
            raise HTTPException(status_code=409, detail="El username ya está registrado")

        user = User(
            username=payload.username,
            email=payload.email,
            display_name=payload.display_name,
            bio=payload.bio,
            avatar_url=payload.avatar_url,
            hashed_password=hash_password(payload.password),
        )
        self.repo.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> User | None:
        return self.repo.get(user_id)

    def list_users(self, skip: int = 0, limit: int = 50) -> list[User]:
        return self.repo.list(skip=skip, limit=limit)

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate_user(self, user_id: int) -> None:
        user = self.repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user.is_active = False
        self.db.commit()

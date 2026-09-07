from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def authenticate(self, username_or_email: str, password: str) -> str | None:
        user = self.users.get_by_email(username_or_email)
        if not user:
            user = self.users.get_by_username(username_or_email)

        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None

        return create_access_token(str(user.id))

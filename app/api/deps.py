from typing import Generator
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="identity-service/api/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER, options={"require": ["sub", "exp", "iss"]},
        )
        identity_user_id = str(UUID(str(payload["sub"])))
    except (InvalidTokenError, ValueError, KeyError) as exc:
        raise credentials_error from exc

    users = UserRepository(db)
    user = users.get_by_identity_user_id(identity_user_id)
    email = payload.get("email")
    if not user and isinstance(email, str):
        # One-time bridge: retain existing local PK and all its relationships.
        user = users.get_by_email(email)
        if user and user.identity_user_id is None:
            user.identity_user_id = identity_user_id
            db.commit()
            db.refresh(user)
    if not user:
        username = payload.get("username") or payload.get("preferred_username")
        if not isinstance(username, str) or not username.strip():
            username = f"user-{identity_user_id[:8]}"
        username = username.strip()[:50]
        if users.get_by_username(username):
            username = f"user-{identity_user_id[:8]}"
        user = User(
            identity_user_id=identity_user_id, username=username,
            email=email if isinstance(email, str) else None,
            display_name=payload.get("display_name") or payload.get("name") or username,
        )
        try:
            users.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError as exc:
            db.rollback()
            raise credentials_error from exc
    if not user.is_active:
        raise credentials_error
    return user

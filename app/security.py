from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)
ACCESS_TOKEN_MINUTES = 60


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user: User) -> str:
    if not settings.jwt_secret_key:
        raise HTTPException(status_code=503, detail="JWT_SECRET_KEY is not configured")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not settings.jwt_secret_key:
        if not settings.jwt_secret_key:
            raise HTTPException(status_code=503, detail="JWT_SECRET_KEY is not configured")
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise unauthorized
    except InvalidTokenError as exc:
        raise unauthorized from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_roles(*roles: str):
    def role_dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return role_dependency

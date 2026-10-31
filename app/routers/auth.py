from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, PasswordChange, StudentAccountCreate, TokenOut, UserOut
from app.security import ACCESS_TOKEN_MINUTES, create_access_token, get_current_user, hash_password, require_roles, verify_password

router = APIRouter(prefix="/api/v1", tags=["authentication"])


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username.strip().lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    return TokenOut(access_token=create_access_token(user), expires_in=ACCESS_TOKEN_MINUTES * 60)


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.commit()


@router.post("/admin/students", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentAccountCreate,
    _admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = User(
        username=payload.username.strip().lower(),
        password_hash=hash_password(payload.password),
        role="student",
        student_id=payload.student_id,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or student_id already exists") from exc
    db.refresh(user)
    return user

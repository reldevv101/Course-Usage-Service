from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, UsageRecord, User
from app.schemas import UsageCreate, UsageOut, UsagePatch
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/usage-records", tags=["usage"])


@router.post("", response_model=UsageOut, status_code=201)
def create_usage(payload: UsageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "student":
        student_id = user.student_id
        if payload.student_id is not None and payload.student_id != student_id:
            raise HTTPException(status_code=403, detail="Students can only record usage for themselves")
    else:
        student_id = payload.student_id
        if student_id is None:
            raise HTTPException(status_code=422, detail="Admin must provide student_id")
    course = db.get(Course, payload.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.is_active:
        raise HTTPException(status_code=409, detail="Course is inactive")
    record = UsageRecord(**payload.model_dump(exclude={"student_id"}), student_id=student_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[UsageOut])
def list_usage(
    student_id: str | None = None,
    course_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(UsageRecord).order_by(UsageRecord.recorded_at.desc()).limit(limit).offset(offset)
    if user.role == "student":
        if student_id is not None and student_id != user.student_id:
            raise HTTPException(status_code=403, detail="Students can only view their own usage")
        query = query.where(UsageRecord.student_id == user.student_id)
    elif student_id:
        query = query.where(UsageRecord.student_id == student_id)
    if course_id:
        query = query.where(UsageRecord.course_id == course_id)
    return db.scalars(query).all()


@router.get("/{usage_id}", response_model=UsageOut)
def get_usage(usage_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.get(UsageRecord, usage_id)
    if not record or (user.role == "student" and record.student_id != user.student_id):
        raise HTTPException(status_code=404, detail="Usage record not found")
    return record


@router.patch("/{usage_id}", response_model=UsageOut, dependencies=[Depends(require_roles("admin"))])
def patch_usage(usage_id: str, payload: UsagePatch, db: Session = Depends(get_db)):
    record = db.get(UsageRecord, usage_id)
    if not record:
        raise HTTPException(status_code=404, detail="Usage record not found")
    if record.invoice is not None:
        raise HTTPException(status_code=409, detail="Billed usage records cannot be changed")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{usage_id}", status_code=204, dependencies=[Depends(require_roles("admin"))])
def delete_usage(usage_id: str, db: Session = Depends(get_db)):
    record = db.get(UsageRecord, usage_id)
    if not record:
        raise HTTPException(status_code=404, detail="Usage record not found")
    if record.invoice is not None:
        raise HTTPException(status_code=409, detail="Billed usage records cannot be deleted")
    db.delete(record)
    db.commit()
    return Response(status_code=204)

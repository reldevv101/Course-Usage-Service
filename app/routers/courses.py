from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course
from app.schemas import CourseCreate, CourseOut, CoursePatch
from app.security import require_api_key

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


@router.post("", response_model=CourseOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    course = Course(**payload.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="course_code already exists") from exc
    db.refresh(course)
    return course


@router.get("", response_model=list[CourseOut])
def list_courses(active: bool | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = select(Course).order_by(Course.created_at.desc()).limit(limit).offset(offset)
    if active is not None:
        query = query.where(Course.is_active.is_(active))
    return db.scalars(query).all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: str, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseOut, dependencies=[Depends(require_api_key)])
def replace_course(course_id: str, payload: CourseCreate, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in payload.model_dump().items():
        setattr(course, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="course_code already exists") from exc
    db.refresh(course)
    return course


@router.patch("/{course_id}", response_model=CourseOut, dependencies=[Depends(require_api_key)])
def patch_course(course_id: str, payload: CoursePatch, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "name" and value is not None:
            value = value.strip()
            if not value:
                raise HTTPException(status_code=422, detail="name must not be blank")
        setattr(course, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="course_code already exists") from exc
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_course(course_id: str, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.usage_records:
        raise HTTPException(status_code=409, detail="Course has usage history; deactivate it instead")
    db.delete(course)
    db.commit()
    return Response(status_code=204)

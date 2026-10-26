from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Invoice, UsageRecord


def create_invoice(db: Session, usage_record_id: str) -> Invoice:
    record = db.scalar(select(UsageRecord).where(UsageRecord.id == usage_record_id).with_for_update())
    if record is None:
        raise HTTPException(status_code=404, detail="Usage record not found")
    if db.scalar(select(Invoice.id).where(Invoice.usage_record_id == usage_record_id)):
        raise HTTPException(status_code=409, detail="Usage record has already been billed")

    hours = Decimal(record.study_hours)
    study_cost = int(hours * settings.study_rate_per_hour)
    material_cost = record.material_accesses * settings.material_rate_per_access
    quiz_cost = record.quizzes_completed * settings.quiz_rate_per_completion
    invoice = Invoice(
        usage_record_id=record.id,
        student_id=record.student_id,
        course_id=record.course_id,
        study_hours=hours,
        material_accesses=record.material_accesses,
        quizzes_completed=record.quizzes_completed,
        study_rate_per_hour=settings.study_rate_per_hour,
        material_rate_per_access=settings.material_rate_per_access,
        quiz_rate_per_completion=settings.quiz_rate_per_completion,
        study_cost=study_cost,
        material_cost=material_cost,
        quiz_cost=quiz_cost,
        total_cost=study_cost + material_cost + quiz_cost,
        currency="IDR",
    )
    db.add(invoice)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Usage record has already been billed") from exc
    db.refresh(invoice)
    return invoice

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    course_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    usage_records: Mapped[list["UsageRecord"]] = relationship(back_populates="course")


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        CheckConstraint("study_hours >= 0", name="ck_usage_study_hours_nonnegative"),
        CheckConstraint("material_accesses >= 0", name="ck_usage_material_accesses_nonnegative"),
        CheckConstraint("quizzes_completed >= 0", name="ck_usage_quizzes_nonnegative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id: Mapped[str] = mapped_column(String(20), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), index=True)
    study_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    material_accesses: Mapped[int] = mapped_column(Integer)
    quizzes_completed: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    course: Mapped[Course] = relationship(back_populates="usage_records")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="usage_record", uselist=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("usage_record_id", name="uq_invoice_usage_record"),
        CheckConstraint("total_cost = study_cost + material_cost + quiz_cost", name="ck_invoice_total_matches_breakdown"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    usage_record_id: Mapped[str] = mapped_column(ForeignKey("usage_records.id", ondelete="RESTRICT"), index=True)
    student_id: Mapped[str] = mapped_column(String(20))
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    study_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    material_accesses: Mapped[int] = mapped_column(Integer)
    quizzes_completed: Mapped[int] = mapped_column(Integer)
    study_rate_per_hour: Mapped[int] = mapped_column(BigInteger)
    material_rate_per_access: Mapped[int] = mapped_column(BigInteger)
    quiz_rate_per_completion: Mapped[int] = mapped_column(BigInteger)
    study_cost: Mapped[int] = mapped_column(BigInteger)
    material_cost: Mapped[int] = mapped_column(BigInteger)
    quiz_cost: Mapped[int] = mapped_column(BigInteger)
    total_cost: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="IDR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    usage_record: Mapped[UsageRecord] = relationship(back_populates="invoice")

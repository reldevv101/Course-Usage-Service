import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


CourseCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")]
StudentId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=20, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")]


class CourseCreate(BaseModel):
    course_code: CourseCode
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class CoursePatch(BaseModel):
    course_code: CourseCode | None = None
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    is_active: bool | None = None

    @field_validator("course_code", "name", "is_active")
    @classmethod
    def required_patch_fields_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("field must not be blank")
        return value


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    course_code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UsageCreate(BaseModel):
    student_id: StudentId
    course_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")
    study_hours: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    material_accesses: int = Field(ge=0, le=2_147_483_647)
    quizzes_completed: int = Field(ge=0, le=2_147_483_647)

    @field_validator("study_hours")
    @classmethod
    def finite_hours(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("study_hours must be finite")
        return value


class UsagePatch(BaseModel):
    study_hours: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    material_accesses: int | None = Field(default=None, ge=0, le=2_147_483_647)
    quizzes_completed: int | None = Field(default=None, ge=0, le=2_147_483_647)

    @model_validator(mode="before")
    @classmethod
    def explicit_values_cannot_be_null(cls, value):
        if isinstance(value, dict) and any(item is None for item in value.values()):
            raise ValueError("usage values cannot be null")
        return value

    @field_validator("study_hours")
    @classmethod
    def finite_patch_hours(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not value.is_finite():
            raise ValueError("study_hours must be finite")
        return value


class UsageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    course_id: str
    study_hours: Decimal
    material_accesses: int
    quizzes_completed: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    usage_record_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    usage_record_id: str
    student_id: str
    course_id: str
    study_hours: Decimal
    material_accesses: int
    quizzes_completed: int
    study_rate_per_hour: int
    material_rate_per_access: int
    quiz_rate_per_completion: int
    study_cost: int
    material_cost: int
    quiz_cost: int
    total_cost: int
    currency: str
    created_at: datetime

    @classmethod
    def from_invoice(cls, invoice):
        return cls.model_validate(invoice)

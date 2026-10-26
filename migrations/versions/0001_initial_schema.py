"""Create initial Course Usage Service schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("course_code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_courses_course_code", "courses", ["course_code"], unique=True)

    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=20), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("study_hours", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("material_accesses", sa.Integer(), nullable=False),
        sa.Column("quizzes_completed", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("study_hours >= 0", name="ck_usage_study_hours_nonnegative"),
        sa.CheckConstraint("material_accesses >= 0", name="ck_usage_material_accesses_nonnegative"),
        sa.CheckConstraint("quizzes_completed >= 0", name="ck_usage_quizzes_nonnegative"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_records_student_id", "usage_records", ["student_id"], unique=False)
    op.create_index("ix_usage_records_course_id", "usage_records", ["course_id"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usage_record_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=20), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("study_hours", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("material_accesses", sa.Integer(), nullable=False),
        sa.Column("quizzes_completed", sa.Integer(), nullable=False),
        sa.Column("study_rate_per_hour", sa.BigInteger(), nullable=False),
        sa.Column("material_rate_per_access", sa.BigInteger(), nullable=False),
        sa.Column("quiz_rate_per_completion", sa.BigInteger(), nullable=False),
        sa.Column("study_cost", sa.BigInteger(), nullable=False),
        sa.Column("material_cost", sa.BigInteger(), nullable=False),
        sa.Column("quiz_cost", sa.BigInteger(), nullable=False),
        sa.Column("total_cost", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("total_cost = study_cost + material_cost + quiz_cost", name="ck_invoice_total_matches_breakdown"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usage_record_id"], ["usage_records.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usage_record_id", name="uq_invoice_usage_record"),
    )
    op.create_index("ix_invoices_usage_record_id", "invoices", ["usage_record_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_invoices_usage_record_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_usage_records_course_id", table_name="usage_records")
    op.drop_index("ix_usage_records_student_id", table_name="usage_records")
    op.drop_table("usage_records")
    op.drop_index("ix_courses_course_code", table_name="courses")
    op.drop_table("courses")

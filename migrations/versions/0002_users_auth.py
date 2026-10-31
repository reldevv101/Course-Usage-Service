"""Add accounts for admin and student login."""

from alembic import op
import sqlalchemy as sa

revision = "0002_users_auth"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" in inspector.get_table_names():
        # Development may already have created this table via SQLAlchemy
        # metadata before PostgreSQL DDL was restricted to Alembic.
        existing_columns = {column["name"] for column in inspector.get_columns("users")}
        expected_columns = {"id", "username", "password_hash", "role", "student_id", "is_active", "created_at"}
        missing_columns = expected_columns - existing_columns
        if missing_columns:
            raise RuntimeError(f"Existing users table is incomplete; missing columns: {sorted(missing_columns)}")
        existing_indexes = {index["name"] for index in inspector.get_indexes("users")}
        if "ix_users_username" not in existing_indexes:
            op.create_index("ix_users_username", "users", ["username"], unique=True)
    else:
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("student_id", sa.String(length=20), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("role IN ('admin', 'student')", name="ck_users_role"),
            sa.CheckConstraint("(role = 'admin' AND student_id IS NULL) OR (role = 'student' AND student_id IS NOT NULL)", name="ck_users_student_id_for_role"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("student_id", name="uq_users_student_id"),
        )
        op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    # The table may have existed before this revision and been adopted by it.
    # Preserve account data rather than risk dropping a pre-existing table.
    pass

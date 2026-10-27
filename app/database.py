from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_options = {"pool_pre_ping": True}
if settings.database_url.startswith("postgresql"):
    if settings.db_pool_mode == "transaction":
        # Supabase's transaction pooler is designed for short-lived serverless
        # requests: keep one app-side connection and disable Psycopg prepares.
        engine_options.update(pool_size=1, max_overflow=0, pool_recycle=1800)
        connect_args.update(prepare_threshold=None, sslmode="require")
    else:
        engine_options.update(pool_size=3, max_overflow=2, pool_recycle=1800)
engine = create_engine(settings.database_url, connect_args=connect_args, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

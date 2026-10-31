from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import event

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 - register SQLAlchemy models before create_all
from app.routers import auth, billing, courses, usage


if engine.url.drivername.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


if settings.environment == "development" and engine.url.drivername.startswith("sqlite"):
    # Local SQLite is convenient for first-run development. PostgreSQL schemas
    # must be changed only through Alembic migrations.
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Course Usage Service",
    description="REST API simulasi metering penggunaan pembelajaran dan billing berbasis pemakaian.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(courses.router)
app.include_router(usage.router)
app.include_router(billing.router)
app.include_router(auth.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

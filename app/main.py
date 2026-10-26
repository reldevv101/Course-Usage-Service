from fastapi import FastAPI
from sqlalchemy import event

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 - register SQLAlchemy models before create_all
from app.routers import billing, courses, usage


if engine.url.drivername.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


if settings.environment == "development":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Course Usage Service",
    description="REST API simulasi metering penggunaan pembelajaran dan billing berbasis pemakaian.",
    version="0.1.0",
)
app.include_router(courses.router)
app.include_router(usage.router)
app.include_router(billing.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

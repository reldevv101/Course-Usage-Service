import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./course_usage.db")
    environment: str = os.getenv("ENVIRONMENT", "development").lower()
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    db_pool_mode: str = os.getenv("DB_POOL_MODE", "session").lower()
    frontend_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    )
    study_rate_per_hour: int = int(os.getenv("STUDY_RATE_PER_HOUR", "2000"))
    material_rate_per_access: int = int(os.getenv("MATERIAL_RATE_PER_ACCESS", "500"))
    quiz_rate_per_completion: int = int(os.getenv("QUIZ_RATE_PER_COMPLETION", "1000"))

    def __post_init__(self):
        # Supabase supplies PostgreSQL URLs in either scheme; explicitly select
        # psycopg 3 so the driver is stable across local/cloud environments.
        if self.database_url.startswith("postgres://"):
            object.__setattr__(self, "database_url", self.database_url.replace("postgres://", "postgresql+psycopg://", 1))
        elif self.database_url.startswith("postgresql://"):
            object.__setattr__(self, "database_url", self.database_url.replace("postgresql://", "postgresql+psycopg://", 1))
        if self.db_pool_mode not in {"session", "transaction"}:
            raise ValueError("DB_POOL_MODE must be either 'session' or 'transaction'")
        if min(self.study_rate_per_hour, self.material_rate_per_access, self.quiz_rate_per_completion) < 0:
            raise ValueError("Billing rates must be non-negative integers")


settings = Settings()

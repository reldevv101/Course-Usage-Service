from fastapi import Header, HTTPException

from app.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    # Local development is convenient by default. Deployed environments fail
    # closed if the key has not been configured.
    if settings.environment == "development":
        return
    if not settings.api_key:
        raise HTTPException(status_code=503, detail="API key protection is not configured")
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

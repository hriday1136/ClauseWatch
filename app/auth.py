import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
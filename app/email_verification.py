import hashlib
import hmac
import time
import uuid

from app.config import settings


def generate_verification_token(user_id: uuid.UUID, expires_in_seconds: int = 86400 * 7) -> str:
    expires_at = int(time.time()) + expires_in_seconds
    payload = f"{user_id}:{expires_at}"
    signature = hmac.new(settings.email_verification_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{user_id}.{expires_at}.{signature}"


def verify_verification_token(token: str) -> uuid.UUID | None:
    try:
        user_id_str, expires_at_str, signature = token.split(".", 2)
        user_id = uuid.UUID(user_id_str)
        expires_at = int(expires_at_str)
    except (ValueError, TypeError):
        return None

    if time.time() > expires_at:
        return None

    payload = f"{user_id}:{expires_at}"
    expected_signature = hmac.new(settings.email_verification_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    return user_id
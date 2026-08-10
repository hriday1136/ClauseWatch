import hashlib
import hmac
import uuid
import time

from app.config import settings


def generate_download_token(contract_id: uuid.UUID, expires_in_seconds: int = 3600) -> str:
    expires_at = int(time.time()) + expires_in_seconds
    message = f"{contract_id}:{expires_at}"
    signature = hmac.new(settings.download_link_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"{expires_at}.{signature}"

def verify_download_token(contract_id: uuid.UUID, token: str) -> bool:
    try:
        expires_at_str, signature = token.split(".",1)
        expires_at = int(expires_at_str)
    except ValueError:
        return False

    if time.time() > expires_at:
        return False

    message = f"{contract_id}:{expires_at}"
    expected_signature = hmac.new(settings.download_link_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

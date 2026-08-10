import hashlib
import hmac
import json

import httpx


def sign_payload(secret: str, payload_bytes: bytes) -> str:
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

def send_webhook(url: str, secret: str, payload: dict) -> None:
    payload_bytes = json.dumps(payload, default=str).encode()
    signature = sign_payload(secret, payload_bytes)

    response = httpx.post(
        url,
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-ClauseWatch-Signature": signature,
        },
        timeout=10,
    )
    response.raise_for_status()
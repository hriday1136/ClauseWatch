import hashlib
import secrets
import base64
import hmac
import os

PBKDF2_ITERATIONS = 600_000

def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        iterations_str, salt_b64, derived_b64 = password_hash.split("$")
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(derived_b64)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(actual, expected)
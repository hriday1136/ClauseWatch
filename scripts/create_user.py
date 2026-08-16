import sys
import uuid

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def create_user(tenant_id: str, email: str, password: str) -> None:
    db = SessionLocal()
    try:
        user = User(
            tenant_id=uuid.UUID(tenant_id),
            email=email,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"user id: {user.id}")
        print(f"email: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: python -m scripts.create_user <tenant-id> <email> <password>")
        sys.exit(1)
    create_user(sys.argv[1], sys.argv[2], sys.argv[3])
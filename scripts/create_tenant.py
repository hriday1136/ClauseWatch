import sys

from app.models import Tenant
from app.security import generate_api_key, hash_api_key
from app.database import SessionLocal

def create_tenant(name: str, notification_email: str) -> Tenant:
    # Generate a secure API key
    raw_key = generate_api_key()
    tenant= Tenant(
        name=name, 
        api_key_hash=hash_api_key(raw_key), 
        notification_email=notification_email
        )

    db = SessionLocal()
    try:
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    finally:
        db.close()

    print(f"tenant id: {tenant.id}")
    print(f"api key (save this now, it won't be shown again): {raw_key}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_tenant.py <tenant_name> <notification_email>")
        sys.exit(1)

    create_tenant(sys.argv[1], sys.argv[2])
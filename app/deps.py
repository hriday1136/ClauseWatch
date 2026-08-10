from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.security import hash_api_key

def get_current_tenant(
        x_api_key: str = Header(...),
        db: Session = Depends(get_db)
) -> Tenant:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.api_key_hash == hash_api_key(x_api_key))
        .first()
    )
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid api key",
        )
    return tenant
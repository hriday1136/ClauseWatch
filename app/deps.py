import uuid

import jwt as pyjwt

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tenant
from app.security import hash_api_key
from app.auth import decode_access_token
from app.models import User

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

def get_current_user(
        authorization: str = Header(default=""),
        db: Session = Depends(get_db)
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid authorization, header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token")

    user = db.query(User).filter(User.id == uuid.UUID(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")

    return user

def get_current_tenant_flexible(
    x_api_key: str | None = Header(default=None),
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> Tenant:
    if x_api_key:
        tenant = db.query(Tenant).filter(Tenant.api_key_hash == hash_api_key(x_api_key)).first()
        if tenant is None:
            raise HTTPException(status_code=401, detail="invalid api key")
        return tenant

    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        try:
            payload = decode_access_token(token)
        except pyjwt.PyJWTError:
            raise HTTPException(status_code=401, detail="invalid or expired token")
        tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(payload["tenant_id"])).first()
        if tenant is None:
            raise HTTPException(status_code=401, detail="tenant not found")
        return tenant

    raise HTTPException(status_code=401, detail="authentication required")
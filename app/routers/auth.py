import logging
import hmac
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.database import get_db
from app.deps import get_current_user
from app.models import User, Tenant, Contract, Clause, Party, WebhookSubscription
from app.security import verify_password, generate_api_key, hash_api_key, hash_password
from app.password_reset import generate_reset_token, verify_reset_token
from app.email import send_password_reset_email, send_verification_email
from app.config import settings
from app.email_verification import generate_verification_token, verify_verification_token
from app.storage import delete_file
from app.contract_deletion import delete_contract_fully

SAMPLE_ACCOUNT_EMAIL = "hridayadani1136@gmail.com"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: str
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SignupIn(BaseModel):
    company_name: str
    email: str
    password: str


class SignupOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordIn(BaseModel):
    email: str


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

class DemoLoginIn(BaseModel):
    owner_key: str | None = None


@router.post("/signup", response_model=SignupOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Unable to create account with the provided details. If you already have an account, try logging in.")

    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="password must be at least 8 characters")

    raw_key = generate_api_key()
    tenant = Tenant(name=payload.company_name, api_key_hash=hash_api_key(raw_key), notification_email=payload.email)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    verify_token = generate_verification_token(user.id)
    verify_link = f"{settings.frontend_url}/verify-email?token={verify_token}"
    try:
        send_verification_email(user.email, verify_link)
    except Exception as e:
        logger.error(f"failed to send verification email to {user.email}: {e}")

    token = create_access_token(user.id, tenant.id)
    return SignupOut(access_token=token)

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")

    token = create_access_token(user.id, user.tenant_id)
    return LoginOut(access_token=token)

@router.post("/demo-login", response_model=LoginOut)
def demo_login(payload: DemoLoginIn, db: Session = Depends(get_db)):
    template_tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(settings.template_tenant_id)).first()
    if template_tenant is None:
        raise HTTPException(status_code=500, detail="demo is not configured")

    if payload.owner_key and hmac.compare_digest(payload.owner_key, settings.demo_owner_key):
        owner_user = db.query(User).filter(User.tenant_id == template_tenant.id).first()
        if owner_user is None:
            raise HTTPException(status_code=500, detail="template tenant has no user")
        token = create_access_token(owner_user.id, template_tenant.id)
        return LoginOut(access_token=token)

    demo_tenant = Tenant(
        name=f"Demo {uuid.uuid4().hex[:8]}",
        api_key_hash=hash_api_key(generate_api_key()),
        is_demo=True,
    )
    db.add(demo_tenant)
    db.commit()
    db.refresh(demo_tenant)

    demo_user = User(
        tenant_id=demo_tenant.id,
        email=f"demo-{demo_tenant.id}@clausewatch.local",
        password_hash=hash_password(secrets.token_urlsafe(32)),
    )
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)

    for template_contract in db.query(Contract).filter(Contract.tenant_id == template_tenant.id).all():
        new_contract = Contract(
            tenant_id=demo_tenant.id,
            file_ref=template_contract.file_ref,
            original_filename=template_contract.original_filename,
            file_type=template_contract.file_type,
            status=template_contract.status,
        )
        db.add(new_contract)
        db.commit()
        db.refresh(new_contract)

        for party in db.query(Party).filter(Party.contract_id == template_contract.id).all():
            db.add(Party(contract_id=new_contract.id, name=party.name, role=party.role))

        for clause in db.query(Clause).filter(Clause.contract_id == template_contract.id).all():
            db.add(Clause(
                contract_id=new_contract.id,
                type=clause.type,
                value=clause.value,
                original_value=clause.original_value,
                confidence=clause.confidence,
                source_text_span=clause.source_text_span,
                is_corrected=clause.is_corrected,
                needs_review=clause.needs_review,
            ))
        db.commit()

    token = create_access_token(demo_user.id, demo_tenant.id)
    return LoginOut(access_token=token)

@router.post("/demo-logout", status_code=204)
def demo_logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant is None or not tenant.is_demo:
        return Response(status_code=204)

    contracts = db.query(Contract).filter(Contract.tenant_id == tenant.id).all()
    for contract in contracts:
        delete_contract_fully(contract, db)
    db.flush()

    db.query(WebhookSubscription).filter(WebhookSubscription.tenant_id == tenant.id).delete()
    db.query(User).filter(User.tenant_id == tenant.id).delete()
    db.query(Tenant).filter(Tenant.id == tenant.id).delete()
    db.commit()
    return Response(status_code=204)

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is not None:
        token = generate_reset_token(user.id)
        reset_link = f"{settings.frontend_url}/reset-password?token={token}"
        send_password_reset_email(user.email, reset_link)

    return {"message": "If an account with that email exists, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    user_id = verify_reset_token(payload.token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="invalid or expired reset link")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="password must be at least 8 characters")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="invalid or expired reset link")

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully."}

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {"user_id": str(user.id), "email": user.email, "tenant_id": str(user.tenant_id)}

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user_id = verify_verification_token(token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="invalid or expired verification link")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="invalid or expired verification link")

    user.email_verified = True
    db.commit()

    return {"message": "Email verified successfully."}

@router.post("/rotate-api-key")
def rotate_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    raw_key = generate_api_key()
    tenant.api_key_hash = hash_api_key(raw_key)
    db.commit()

    return {"api_key": raw_key}


class DeleteAccountIn(BaseModel):
    password: str


@router.post("/delete-account", status_code=204)
def delete_account(
    payload: DeleteAccountIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.email == SAMPLE_ACCOUNT_EMAIL:
        raise HTTPException(status_code=403, detail="This is a sample account and cannot be deleted.")
    
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="incorrect password")

    tenant_id = user.tenant_id

    contracts = db.query(Contract).filter(Contract.tenant_id == tenant_id).all()
    for contract in contracts:
        delete_contract_fully(contract, db)
    db.flush()

    db.query(WebhookSubscription).filter(WebhookSubscription.tenant_id == tenant_id).delete()
    db.query(User).filter(User.tenant_id == tenant_id).delete()
    db.query(Tenant).filter(Tenant.id == tenant_id).delete()

    db.commit()
    return Response(status_code=204)
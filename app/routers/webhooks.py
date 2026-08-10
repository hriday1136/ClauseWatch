import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_tenant
from app.schemas import WebhookSubscriptionIn, WebhookSubscriptionOut
from app.models import Tenant, WebhookSubscription
from app.security import generate_api_key

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/subscribe", response_model=WebhookSubscriptionOut)
def subscribe_webhook(
    payload: WebhookSubscriptionIn,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    subscription = WebhookSubscription(
        tenant_id=tenant.id,
        url=str(payload.url),
        secret=generate_api_key()
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.post("/{subscription_id}/rotate-secret", response_model=WebhookSubscriptionOut)
def rotate_webhook_secret(
    subscription_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    subscription = (
        db.query(WebhookSubscription)
        .filter(WebhookSubscription.id == subscription_id, WebhookSubscription.tenant_id == tenant.id)
        .first()
    )
    if subscription is None:
        raise HTTPException(status_code=404, detail="webhook subscription not found")

    subscription.secret = generate_api_key()
    db.commit()
    db.refresh(subscription)
    return subscription
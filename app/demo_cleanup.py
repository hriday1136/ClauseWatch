from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.contract_deletion import delete_contract_fully
from app.models import Contract, Tenant, User, WebhookSubscription


def cleanup_stale_demo_tenants(db: Session, older_than_hours: int = 2) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    stale_tenants = (
        db.query(Tenant)
        .filter(Tenant.is_demo == True, Tenant.created_at <= cutoff)
        .all()
    )

    for tenant in stale_tenants:
        contracts = db.query(Contract).filter(Contract.tenant_id == tenant.id).all()
        for contract in contracts:
            delete_contract_fully(contract, db)
        db.query(WebhookSubscription).filter(WebhookSubscription.tenant_id == tenant.id).delete()
        db.query(User).filter(User.tenant_id == tenant.id).delete()
        db.query(Tenant).filter(Tenant.id == tenant.id).delete()

    db.commit()
    return len(stale_tenants)
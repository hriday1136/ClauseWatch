import logging

from datetime import date, timedelta, timezone, datetime

from sqlalchemy.orm import Session

from app.models import Clause, ClauseType, Contract, ContractStatus, Reminder, Tenant, WebhookSubscription
from app.webhooks import send_webhook
from app.email import send_reminder_email
from app.metrics import reminders_dispatched_total, webhook_dispatch_failures_total

logger = logging.getLogger(__name__)

REMINDER_THRESHOLD_DAYS = [90, 60,30]

def sync_reminders(db: Session) -> int:
    created_count = 0

    renewal_clauses = (
        db.query(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .join(Tenant, Contract.tenant_id == Tenant.id)
        .filter(
            Clause.type == ClauseType.renewal_date,
            Contract.status == ContractStatus.completed,
            Tenant.is_demo == False,
        )
        .all()
    )

    for clause in renewal_clauses:
        renewal_date_str = clause.value.get("date")
        if not renewal_date_str:
            continue
        renewal_date = date.fromisoformat(renewal_date_str)

        for threshold_days in REMINDER_THRESHOLD_DAYS:
            existing = (
                db.query(Reminder)
                .filter(Reminder.clause_id == clause.id, Reminder.threshold_days == threshold_days)
                .first()
            )
            if existing is not None:
                continue

            trigger_date = renewal_date - timedelta(days=threshold_days)
            db.add(Reminder(
                contract_id = clause.contract_id,
                clause_id = clause.id,
                trigger_date = trigger_date,
                threshold_days = threshold_days
            ))
            created_count += 1

    db.commit()
    return created_count

def dispatch_due_reminders(db: Session) -> int:
    dispatched_count = 0

    due_reminders = (
        db.query(Reminder)
        .filter(Reminder.trigger_date <=date.today(), Reminder.sent_at.is_(None))
        .all()
    )

    for reminder in due_reminders:
        contract = db.query(Contract).filter(Contract.id == reminder.contract_id).first()
        clause = db.query(Clause).filter(Clause.id == reminder.clause_id).first()
        tenant = db.query(Tenant).filter(Tenant.id == contract.tenant_id).first()

        renewal_date = clause.value.get("date", "unkown")
        payload = {
            "event": "renewal_reminder",
            "contract_id": str(contract.id),
            "original_filename": contract.original_filename,
            "renewal_date": renewal_date,
            "threshold_days": reminder.threshold_days
        }

        subscriptions = (
            db.query(WebhookSubscription)
            .filter(WebhookSubscription.tenant_id == tenant.id)
            .all()
        )
        for subscription in subscriptions:
            try:
                send_webhook(subscription.url, subscription.secret, payload)
            except Exception as e:
                webhook_dispatch_failures_total.inc()
                print(f"webhook dispatch failed for subscription {subscription.id}: {e}")

        if tenant.notification_email:
            try:
                send_reminder_email(
                    tenant.notification_email,
                    contract.original_filename,
                    renewal_date,
                    reminder.threshold_days
                )
            except Exception as e:
                print(f"email dispatch failed for tenant {tenant.id}: {e}")

        reminder.sent_at = datetime.now(timezone.utc)
        dispatched_count += 1
        reminders_dispatched_total.inc()

    db.commit()
    return dispatched_count
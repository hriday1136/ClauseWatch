from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.demo_cleanup import cleanup_stale_demo_tenants
from app.reminders import dispatch_due_reminders, sync_reminders

router = APIRouter(prefix="/cron", tags=["cron"])


@router.get("/daily-maintenance")
def cron_daily_maintenance(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    expected = f"Bearer {settings.cron_secret}"
    if not settings.cron_secret or authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")

    created = sync_reminders(db)
    dispatched = dispatch_due_reminders(db)
    demo_cleaned = cleanup_stale_demo_tenants(db)

    return {"created": created, "dispatched": dispatched, "demo_tenants_cleaned": demo_cleaned}
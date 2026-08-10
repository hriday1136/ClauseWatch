from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.reminders import dispatch_due_reminders, sync_reminders

router = APIRouter(prefix="/cron", tags=["cron"])

@router.get("/sync-reminders")
def cron_sync_reminders(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db)
):
    expected = f"Bearer {settings.cron_secret}"
    if not settings.cron_secret or authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")

    created = sync_reminders(db)
    dispatched = dispatch_due_reminders(db)
    return {"created": created, "dispatched": dispatched}
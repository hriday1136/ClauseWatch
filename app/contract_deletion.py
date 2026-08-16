import logging

from sqlalchemy.orm import Session

from app.models import Contract, Reminder
from app.storage import delete_file

logger = logging.getLogger(__name__)


def delete_contract_fully(contract: Contract, db: Session) -> None:
    db.query(Reminder).filter(Reminder.contract_id == contract.id).delete()

    if contract.file_ref.startswith(f"{contract.tenant_id}/"):
        try:
            delete_file(contract.file_ref)
        except Exception as e:
            logger.error(f"failed to delete storage object for contract {contract.id}: {e}")
    db.delete(contract)
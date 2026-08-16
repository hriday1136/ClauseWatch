import uuid
import logging

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_tenant_flexible
from app.models import Contract, Tenant, ContractStatus, FileType, Clause, ClauseType
from app.storage import upload_file, download_file, delete_file
from app.persistence import process_contract
from app.schemas import ContractDetailOut, ClauseCorrectionIn, ClauseOut, UpcomingDeadlineOut
from app.download_tokens import generate_download_token, verify_download_token
from app.metrics import contracts_uploaded_total
from app.schemas import ContractSummaryOut
from app.reminders import dispatch_due_reminders, sync_reminders
from app.contract_deletion import delete_contract_fully

from datetime import datetime, timezone, date, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts", tags=["contracts"])

ALLOWED_EXTENSIONS = {".pdf": FileType.pdf, ".docx": FileType.docx}

@router.post("")
def upload_contract(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db)
):
    extension = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    file_type = ALLOWED_EXTENSIONS.get(extension)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only .pdf and .docx files are supported"
        )

    contract_id = uuid.uuid4()
    file_bytes = file.file.read()
    object_key = f"{tenant.id}/{contract_id}/{file.filename}"

    upload_file(object_key, file_bytes, file.content_type or "application/octet-stream")

    contract = Contract(
        id=contract_id,
        tenant_id=tenant.id,
        file_ref=object_key,
        original_filename=file.filename,
        file_type=file_type,
        status=ContractStatus.uploaded
    )

    db.add(contract)
    db.commit()
    db.refresh(contract)

    contracts_uploaded_total.inc()

    process_contract(contract.id, db)
    db.refresh(contract)

    return {
        "id": str(contract.id),
        "status": contract.status.value,
        "file_type": contract.file_type.value,
        "original_filename": contract.original_filename
    }

@router.get("/upcoming-deadlines", response_model=list[UpcomingDeadlineOut])
def upcoming_deadlines(
    days: int = 30,
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db)
):
    cutoff = date.today() + timedelta(days=days)

    results = (
        db.query(Clause, Contract)
        .join(Clause, Clause.contract_id == Contract.id)
        .filter(
            Contract.tenant_id == tenant.id,
            Contract.status == ContractStatus.completed,
            Clause.type == ClauseType.renewal_date
        )
        .all()
    )

    upcoming = []
    for clause, contract in results:
        renewal_date_str = clause.value.get("date")
        if not renewal_date_str:
            continue
        renewal_date = date.fromisoformat(renewal_date_str)
        if renewal_date <= cutoff:
            upcoming.append(UpcomingDeadlineOut(
                contract_id = contract.id,
                original_filename = contract.original_filename,
                renewal_date = renewal_date_str,
                days_until_renewal=(renewal_date - date.today()).days
            ))

    upcoming.sort(key=lambda item: item.days_until_renewal)
    return upcoming

@router.get("", response_model=list[ContractSummaryOut])
def list_contracts(
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db),
):
    return (
        db.query(Contract)
        .filter(Contract.tenant_id == tenant.id)
        .order_by(Contract.created_at.desc())
        .all()
    )

@router.get("/{contract_id}", response_model=ContractDetailOut)
def get_contract(
    contract_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db)
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.tenant_id == tenant.id)
        .first()
    )
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="contract not found"
        )
    return contract

@router.get("/{contract_id}/download-url")
def get_download_url(
    contract_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db)
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.tenant_id == tenant.id)
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="contract not found")

    token = generate_download_token(contract.id)
    return {"download_url": f"/contracts/{contract.id}/download?token={token}"}

@router.get("/{contract_id}/download")
def download_contract_file(contract_id:uuid.UUID, token:str, db:Session=Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="contract not found")

    if not verify_download_token(contract.id, token):
        raise HTTPException(status_code=403, detail="invalid or expired download token")

    file_bytes = download_file(contract.file_ref)
    media_type = (
        "application/pdf" if contract.file_type == FileType.pdf
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    disposition = "inline" if contract.file_type == FileType.pdf else "attachment"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{contract.original_filename}"'}
    )

@router.patch("/{contract_id}/clauses/{clause_id}", response_model=ClauseOut)
def correct_clause(
    contract_id: uuid.UUID,
    clause_id: uuid.UUID,
    correction: ClauseCorrectionIn,
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db)
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.tenant_id == tenant.id)
        .first()
    )
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="contract not found"
        )

    clause = (
        db.query(Clause)
        .filter(Clause.id == clause_id, Clause.contract_id == contract_id)
        .first()
    )
    if clause is None:
        raise HTTPException(
            status_code=404,
            detail="clause not found"
        )

    clause.value = correction.value.model_dump()
    clause.is_corrected = True
    clause.needs_review = False
    clause.corrected_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(clause)

    return clause

@router.post("/{contract_id}/approve", response_model=ContractDetailOut)
def approve_contract(
    contract_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db),
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.tenant_id == tenant.id)
        .first()
    )
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="contract not found"
        )
    if contract.status != ContractStatus.pending_review:
        raise HTTPException(
            status_code=400,
            detail=f"cannot approve contract with status: '{contract.status.value}': must be 'pending_review'"
        )

    contract.status = ContractStatus.completed
    db.commit()
    db.refresh(contract)

    sync_reminders(db)
    dispatch_due_reminders(db)

    return contract

@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db),
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.tenant_id == tenant.id)
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="contract not found")

    delete_contract_fully(contract, db)
    db.commit()
    return Response(status_code=204)

@router.delete("", status_code=204)
def delete_all_contracts(
    tenant: Tenant = Depends(get_current_tenant_flexible),
    db: Session = Depends(get_db),
):
    contracts = db.query(Contract).filter(Contract.tenant_id == tenant.id).all()
    for contract in contracts:
        delete_contract_fully(contract, db)
    db.commit()
    return Response(status_code=204)
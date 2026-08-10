import uuid

from sqlalchemy.orm import Session

from app.extraction import extract_text
from app.llm import extract_contract_data
from app.models import Clause, ClauseType, Contract, ContractStatus, Party
from app. storage import download_file
from app.metrics import contract_extraction_failures_total, contract_extraction_duration_seconds

CONFIDENCE_THRESHOLD: dict[ClauseType, float] = {
    ClauseType.effective_date: 0.95,
    ClauseType.renewal_date: 0.95,
    ClauseType.notice_period: 0.95,
    ClauseType.termination_clause: 0.7,
    ClauseType.payment_terms: 0.95,
}

def process_contract(contact_id: uuid.UUID, db: Session) -> None:
    contract = db.query(Contract).filter(Contract.id == contact_id).first()
    if contract is None:
        raise ValueError(f"contract not found: {contact_id}")

    contract.status = ContractStatus.processing
    db.commit()

    try:
        with contract_extraction_duration_seconds.time():
            file_bytes = download_file(contract.file_ref)
            text = extract_text(file_bytes, contract.file_type)
            result = extract_contract_data(text)

            for party in result.parties:
                db.add(Party(
                    contract_id=contract.id,
                    name=party.name,
                    role=party.role,
                ))

            for clause in result.clauses:
                value_dict = clause.value.model_dump()
                clause_type = ClauseType(clause.type)
                threshold = CONFIDENCE_THRESHOLD[clause_type]

                db.add(Clause(
                    contract_id=contract.id,
                    type=ClauseType(clause.type),
                    value=value_dict,
                    original_value=value_dict,
                    confidence=clause.confidence,
                    source_text_span=clause.source_text_span,
                    needs_review=clause.confidence < threshold
                ))

        contract.status = ContractStatus.pending_review
        db.commit()

    except Exception:
        contract_extraction_failures_total.inc()
        contract.status = ContractStatus.failed
        db.commit()
        raise
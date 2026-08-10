import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import (
    Clause, ClauseType, Contract, ContractStatus, FileType, Tenant, WebhookSubscription,
)
from app.security import generate_api_key, hash_api_key

client = TestClient(app)


def _make_tenant_with_data(db, name):
    raw_key = generate_api_key()
    tenant = Tenant(name=name, api_key_hash=hash_api_key(raw_key))
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    contract = Contract(
        tenant_id=tenant.id,
        file_ref=f"{tenant.id}/fake/contract.pdf",
        original_filename="isolation_test.pdf",
        file_type=FileType.pdf,
        status=ContractStatus.completed,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    clause_value = {"date": "2027-01-01", "days": None, "text": None, "amount": None, "currency": None}
    clause = Clause(
        contract_id=contract.id,
        type=ClauseType.renewal_date,
        value=clause_value,
        original_value=clause_value,
        confidence=1.0,
        source_text_span="test span",
    )
    db.add(clause)

    webhook = WebhookSubscription(tenant_id=tenant.id, url="https://example.com/hook", secret="testsecret")
    db.add(webhook)

    db.commit()
    db.refresh(clause)
    db.refresh(webhook)

    # Extract plain values now, while the session is still open.
    # Never return live ORM objects that a later, closed session can't refresh.
    return {
        "raw_key": raw_key,
        "tenant_id": tenant.id,
        "contract_id": contract.id,
        "clause_id": clause.id,
        "webhook_id": webhook.id,
    }


@pytest.fixture
def two_tenants():
    db = SessionLocal()
    tag = uuid.uuid4().hex[:8]
    a = _make_tenant_with_data(db, f"IsolationTestA-{tag}")
    b = _make_tenant_with_data(db, f"IsolationTestB-{tag}")
    db.close()

    yield a, b

    db = SessionLocal()
    for entry in (a, b):
        db.query(Clause).filter(Clause.contract_id == entry["contract_id"]).delete()
        db.query(Contract).filter(Contract.id == entry["contract_id"]).delete()
        db.query(WebhookSubscription).filter(WebhookSubscription.id == entry["webhook_id"]).delete()
        db.query(Tenant).filter(Tenant.id == entry["tenant_id"]).delete()
    db.commit()
    db.close()


def test_cannot_get_other_tenants_contract(two_tenants):
    a, b = two_tenants
    resp = client.get(f"/contracts/{a['contract_id']}", headers={"X-API-Key": b["raw_key"]})
    assert resp.status_code == 404


def test_cannot_correct_other_tenants_clause(two_tenants):
    a, b = two_tenants
    resp = client.patch(
        f"/contracts/{a['contract_id']}/clauses/{a['clause_id']}",
        headers={"X-API-Key": b["raw_key"]},
        json={"value": {"date": "2099-01-01", "days": None, "text": None, "amount": None, "currency": None}},
    )
    assert resp.status_code == 404


def test_cannot_approve_other_tenants_contract(two_tenants):
    a, b = two_tenants
    resp = client.post(f"/contracts/{a['contract_id']}/approve", headers={"X-API-Key": b["raw_key"]})
    assert resp.status_code == 404


def test_cannot_rotate_other_tenants_webhook_secret(two_tenants):
    a, b = two_tenants
    resp = client.post(f"/webhooks/{a['webhook_id']}/rotate-secret", headers={"X-API-Key": b["raw_key"]})
    assert resp.status_code == 404


def test_upcoming_deadlines_excludes_other_tenant(two_tenants):
    a, b = two_tenants
    resp = client.get("/contracts/upcoming-deadlines?days=100000", headers={"X-API-Key": b["raw_key"]})
    assert resp.status_code == 200
    contract_ids = {item["contract_id"] for item in resp.json()}
    assert str(a["contract_id"]) not in contract_ids


def test_tenant_can_access_own_contract(two_tenants):
    a, b = two_tenants
    resp = client.get(f"/contracts/{a['contract_id']}", headers={"X-API-Key": a["raw_key"]})
    assert resp.status_code == 200
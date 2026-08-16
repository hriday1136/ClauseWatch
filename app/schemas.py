import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic import HttpUrl

from app.models import ClauseType, ContractStatus, FileType
from app.llm import ClauseValue

class PartyOut(BaseModel):
    id: uuid.UUID
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class ClauseOut(BaseModel):
    id: uuid.UUID
    type: ClauseType
    value: dict
    original_value: dict
    confidence: float
    source_text_span:str
    is_corrected: bool
    needs_review: bool
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class ContractDetailOut(BaseModel):
    id: uuid.UUID
    status: ContractStatus
    file_type: FileType
    original_filename: str
    created_at: datetime
    parties: list[PartyOut]
    clauses: list[ClauseOut]

    model_config = ConfigDict(from_attributes=True)

class ClauseCorrectionIn(BaseModel):
    value: ClauseValue

class WebhookSubscriptionIn(BaseModel):
    url: HttpUrl

class WebhookSubscriptionOut(BaseModel):
    id: uuid.UUID
    url: str
    secret: str

    model_config = ConfigDict(from_attributes=True)

class UpcomingDeadlineOut(BaseModel):
    contract_id: uuid.UUID
    original_filename: str
    renewal_date: str
    days_until_renewal: int

class ContractSummaryOut(BaseModel):
    id: uuid.UUID
    status: ContractStatus
    file_type: FileType
    original_filename: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel

from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)

EXTRACTOR_MODEL = "gpt-5.6-terra"

class ExtractedParty(BaseModel):
    name: str
    role: str

class ClauseValue(BaseModel):
    date: str | None = None
    days: int | None = None
    text: str | None = None
    amount: float | None = None
    currency: str | None = None

class ExtractedClause(BaseModel):
    type: Literal["effective_date", "renewal_date", "notice_period", "termination_clause", "payment_terms"]
    value: ClauseValue
    confidence: float
    source_text_span: str

class ContractExtraction(BaseModel):
    parties: list[ExtractedParty]
    clauses: list[ExtractedClause]


EXTRACTION_PROMPT = """You are a contract analysis assistant. Extract structured data \
from the contract text provided by the user.

Extract:
- All named parties, with their role in the contract (e.g. "Client", "Vendor", "Lessee", "Lessor")
- At most one clause per type, for these four types: effective_date, renewal_date, \
notice_period, termination_clause
- Every distinct payment obligation as its own payment_terms clause. There can be zero, \
one, or several — for example a renewal fee and a separate early termination penalty are \
two different payment_terms clauses, not one.

For each clause's value:
- Fill in "date" (ISO 8601, YYYY-MM-DD) for effective_date and renewal_date clauses, \
leave the other value fields null
- Fill in "days" (integer) for notice_period, leave the other value fields null
- Fill in "text" (a concise one or two sentence summary) for termination_clause, \
leave the other value fields null
- For payment_terms: fill in "amount" (a plain number, no currency symbols) and "currency" \
(ISO 4217 code, e.g. "USD") when the contract states a specific figure. If no fixed number \
is stated (e.g. "the then-current published rate applies"), leave amount and currency null \
and instead fill "text" with a concise description. Always mention in the source_text_span \
or description what triggers the payment (e.g. renewal, late payment, early termination).

Also for each clause:
- confidence: your confidence in this extraction, from 0.0 to 1.0
- source_text_span: the exact sentence(s) from the source text this was extracted from

If a clause type genuinely does not appear in the contract, omit it from the clauses list \
rather than guessing. If the contract states multiple candidate values for a single \
single-occurrence clause type (for example, several different notice periods for different \
situations), pick the one most directly tied to renewal or the primary termination right, \
and reflect the ambiguity with a lower confidence score rather than ignoring it."""

def extract_contract_data(contract_text: str) -> ContractExtraction:
    response = client.responses.parse(
        model=EXTRACTOR_MODEL,
        input=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": contract_text}
        ],
        text_format=ContractExtraction,
    )
    return response.output_parsed
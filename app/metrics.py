# All metrics are incremented within the single API process (no separate worker
# process since Celery was removed), so they're all visible via /metrics with
# no cross-process aggregation needed.

from prometheus_client import Counter, Histogram

contracts_uploaded_total = Counter(
    "clausewatch_contracts_uploaded_total",
    "Total number of contracts uploaded"
)

contract_extraction_failures_total = Counter(
    "clausewatch_contract_extraction_failures_total",
    "Total number of contract extraction failures"
)

contract_extraction_duration_seconds = Histogram(
    "clausewatch_contract_extraction_duration_seconds",
    "Time taken to extract and persist a contract's clauses",
)

webhook_dispatch_failures_total = Counter(
    "clausewatch_webhook_dispatch_failures_total",
    "Total number of failed webhook dispatch attempts",
)

reminders_dispatched_total = Counter(
    "clausewatch_reminders_dispatched_total",
    "Total number of reminders successfully dispatched",
)
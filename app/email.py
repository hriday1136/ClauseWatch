import resend

from app.config import settings

resend.api_key = settings.resend_api_key

def send_reminder_email(
    to_email: str,
    contract_filename: str,
    renewal_date: str,
    threshold_days: int
) -> None:
    resend.Emails.send({
        "from": "ClauseWatch <onboarding@resend.dev>",
        "to": [to_email],
        "subject": f"Contract renewal in {threshold_days} days: {contract_filename}",
        "html": (
            f"<p>The contract <strong>{contract_filename}</strong> renews on "
            f"<strong>{renewal_date}</strong> - that's {threshold_days} days from now.</p>"
            f"<p>Log in to ClauseWatch to review the terms before it renews.</p>"
        ),
    })
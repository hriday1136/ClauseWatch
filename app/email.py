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

def send_password_reset_email(to_email: str, reset_link: str) -> None:
    resend.Emails.send({
        "from": "ClauseWatch <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "Reset your ClauseWatch password",
        "html": (
            f"<p>Click the link below to reset your password. This link expires in 1 hour.</p>"
            f'<p><a href="{reset_link}">{reset_link}</a></p>'
            f"<p>If you didn't request this, you can safely ignore this email.</p>"
        ),
    })

def send_verification_email(to_email: str, verify_link: str) -> None:
    resend.Emails.send({
        "from": "ClauseWatch <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "Verify your ClauseWatch email",
        "html": (
            f"<p>Click the link below to verify your email address.</p>"
            f'<p><a href="{verify_link}">{verify_link}</a></p>'
        ),
    })
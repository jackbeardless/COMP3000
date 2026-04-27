"""
email_service.py — sends transactional emails via Resend.
"""
import resend
from config import settings


def send_invite_email(to_email: str, org_name: str, invite_token: str, admin_email: str) -> None:
    resend.api_key = settings.resend_api_key
    invite_url = f"{settings.app_url}/invite?token={invite_token}"
    resend.Emails.send({
        "from": "Vantage OSINT <onboarding@resend.dev>",
        "to": [to_email],
        "subject": f"You've been invited to join {org_name} on Vantage",
        "html": f"""
<p>Hi,</p>
<p><strong>{admin_email}</strong> has invited you to join the organisation
<strong>{org_name}</strong> on Vantage OSINT.</p>
<p>Make sure you are signed in to Vantage with this email address, then click the
link below to accept:</p>
<p><a href="{invite_url}">{invite_url}</a></p>
<p>This invite is tied to your account — do not share this link.</p>
<p>— The Vantage team</p>
""",
    })

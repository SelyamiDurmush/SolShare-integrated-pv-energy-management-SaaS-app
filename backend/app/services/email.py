import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_password_reset_email(to_email: str, token: str, full_name: str):
    
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
        print("WARNING: Email credentials not set. Token is:", token)
        return
    
    msg = EmailMessage() 
    msg["Subject"] = "SolShare - Password Reset Request"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email

    reset_link = f"{settings.FRONTEND_URL}/login/reset-password?token={token}"

    # Email Body
    msg.set_content(f"""\
            Hello {full_name},

            You recently requested to reset your password for your SolShare account. 
            Click the link below to securely set a new password:

            {reset_link}

            This link will expire in {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.
            If you did not request this change, you can safely ignore this email.

            Sincerely,
            The SolShare Team
            """)
    try:
        # Connect to AWS SES and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            print(f"INFO: Password Reset email successfully sent to {to_email}")
    except Exception as e:
        print(f"ERROR: Failed to send email to {to_email}. Error: {str(e)}")
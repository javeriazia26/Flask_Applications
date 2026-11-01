import smtplib
from email.message import EmailMessage
from flask import current_app

def _send(email, subject, body, success_msg, fail_msg):
    cfg = current_app.config
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = cfg["MAIL_USERNAME"]
    message["To"] = email
    message.set_content(body)

    try:
        with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=10) as smtp:
            smtp.starttls()
            smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            smtp.send_message(message)
        return success_msg, "success"
    except (smtplib.SMTPException, OSError) as e:
        current_app.logger.error("Email send failed: %r", e)
        return fail_msg, "error"


def send_verification_email(email, otp):
    body = f"""Hi, {email}
We received your request to verify your email to use JirFlux website.
Your verification code is: {otp}

This code will expire in 5 minutes.

If you didn't create this account, please ignore this email.
"""
    return _send(email, "Verify Your Email", body,
                 "Verification email sent successfully.",
                 "Unable to send verification email. Please try again later.")
    
    

def send_reset_password_email(email, otp):
    mail_server = current_app.config["MAIL_SERVER"]
    mail_port = current_app.config["MAIL_PORT"]
    mail_username = current_app.config["MAIL_USERNAME"]
    mail_password = current_app.config["MAIL_PASSWORD"]

    message = EmailMessage()
    message["Subject"] = "Reset Your Password"
    message["From"] = mail_username
    message["To"] = email

    message.set_content(
        f"""
        Hi, {email}
We received your request to reset your password to use JirFlux website.
Your verification code is: {otp}

This code will expire in 5 minutes.

If you didn't create this account, please ignore this email.
"""
    )

    try:
        with smtplib.SMTP(mail_server, mail_port) as smtp:
            smtp.starttls()
            smtp.login(mail_username, mail_password)
            smtp.send_message(message)

        return "Reset password email sent successfully.", "success"

    except smtplib.SMTPException as e:
        
        return "Unable to send reset password email. Please try again later.", "error"

    except Exception as e:
        
        return "An unexpected error occurred while sending the email.", "error"
    
    
def send_alert_email(email):
    mail_server = current_app.config["MAIL_SERVER"]
    mail_port = current_app.config["MAIL_PORT"]
    mail_username = current_app.config["MAIL_USERNAME"]
    mail_password = current_app.config["MAIL_PASSWORD"]

    message = EmailMessage()
    message["Subject"] = "Alert: Unauthorized Login Attempt"
    message["From"] = mail_username
    message["To"] = email

    message.set_content(
        f"""
        Hi, {email}
        we have noticed an unauthorized login attempt to your JirFlux account. If this was not you, we recommend changing your password immediately and reviewing your account activity. 
        """)
    
    try:
        with smtplib.SMTP(mail_server, mail_port) as smtp:
            smtp.starttls()
            smtp.login(mail_username, mail_password)
            smtp.send_message(message)

        return "Alert email sent successfully.", "success"

    except smtplib.SMTPException as e:
        
        return "Unable to send alert email. Please try again later.", "error"

    except Exception as e:
        
        return "An unexpected error occurred while sending the email.", "error"
    
def send_device_verification_email(email, otp):
    mail_server = current_app.config["MAIL_SERVER"]
    mail_port = current_app.config["MAIL_PORT"]
    mail_username = current_app.config["MAIL_USERNAME"]
    mail_password = current_app.config["MAIL_PASSWORD"]

    message = EmailMessage()
    message["Subject"] = "Verify Your Device"
    message["From"] = mail_username
    message["To"] = email

    message.set_content(
        f"""
        Hi, {email}
We noticed a login attempt from a device we don't recognize. If this was not you, we recommend changing your password immediately and reviewing your account activity to your JirFlux account.
Just to be safe, we sent you this verification code to ensure it's really you trying to access your account.
Your verification code is: {otp}

This code will expire in 5 minutes.

If you didn't create this account, please ignore this email.
"""
    )

    try:
        with smtplib.SMTP(mail_server, mail_port) as smtp:
            smtp.starttls()
            smtp.login(mail_username, mail_password)
            smtp.send_message(message)

        return "Verification device email sent successfully.", "success"

    except smtplib.SMTPException as e:
        
        return "Unable to send verification device email. Please try again later.", "error"

    except Exception as e:
        
        return "An unexpected error occurred while sending the email.", "error"
    

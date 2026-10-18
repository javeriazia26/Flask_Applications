# Verification Routes
from datetime import datetime
import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash

from app import db
from app.models import User, OTP, TrustedDevice
from app.routes.user.notification import create_notification
from app.routes.admin.admin import audit_log_action
from app.services.encryption_service import hash_data
from app.services.otp_service import send_resend_otp, verify_otp

verify_bp = Blueprint("verify", __name__)


# Email Verification
@verify_bp.route("/verify", methods=["GET", "POST"])
def verify():
    if "pending_user_id" not in session:
        flash("No pending verification found.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email_id=session["pending_email"]).first()

    if request.method == "POST":
        otp = request.form.get("otp")

        if not user:
            flash("User not found.", "error")
            session.pop("pending_user_id", None)
            return redirect(url_for("auth.login"))

        message, category = verify_otp(
            user.user_id,
            otp,
            "email-verification"
        )

        if category == "success":
            user.verified = True

            # Generate trusted device token
            device_token = secrets.token_urlsafe(32)

            # Store only the hash in the database
            device_token_hash = hash_data(device_token)

            trusted_device = TrustedDevice(
                device_token_hash=device_token_hash,
                u_id=user.user_id,
                device_name="Known Device"
            )

            db.session.add(trusted_device)

            db.session.commit()
            audit_log_action("device-verified", "credential", user_id=user.user_id, username=user.username)
            create_notification(
                user_id=user.user_id,
                title="Device Verified",
                message="A new device has been verified for your account.",
                notification_type="security"
            )

            # Create login session
            session["user_id"] = user.user_id
            session["username"] = user.username
            session.pop("pending_user_id", None)

            flash(message, category)

            # Redirect and place original token in browser cookie
            if user.u_role == "admin":
                response = redirect(url_for("dash.admin_dash"))
            else:
                response = redirect(url_for("dash.user_dash"))

            response.set_cookie(
                f"device_token_{user.user_id}",
                    device_token,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=60 * 60 * 24 * 30
            )

            return response

        flash(message, category)

    record = OTP.query.filter_by(
        u_id=user.user_id,
        purpose="email-verification"
    ).first()

    expired = False

    if record and record.expires_at <= datetime.utcnow():
        expired = True

    return render_template(
        "auth/verify.html",
        email=user.email_id,
        expired=expired,
        resend_url=url_for("verify.resend_otp")
    )


# Resend Email Verification OTP
@verify_bp.route("/verify/resend", methods=["POST"])
def resend_otp():
    if "pending_user_id" not in session:
        flash("No pending verification found.", "error")
        return redirect(url_for("auth.login"))

    message, category = send_resend_otp(
        session["pending_user_id"],
        purpose="email-verification"
    )

    flash(message, category)

    return redirect(url_for("verify.verify"))


# Send Password Reset OTP
@verify_bp.route("/verify/reset", methods=["GET", "POST"])
def send_reset_otp():
    if "reset_user_id" not in session:
        flash("No pending password reset found.", "error")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["reset_user_id"])

    if not user:
        session.pop("reset_user_id", None)
        flash("User not found.", "error")
        return redirect(url_for("auth.forgot_password"))

    message, category = send_resend_otp(
        user.user_id,
        purpose="password-reset"
    )
    audit_log_action("sent-password-reset-otp", "email-otp", user_id=user.user_id)
    create_notification(
        user_id=user.user_id,
        title="Reset Password",
        message="An OTP has been sent to your email for password reset.",
        notification_type="security"
    )

    flash(message, category)
    return redirect(url_for("verify.verify_reset_otp"))

# Verify Password Reset OTP
@verify_bp.route("/verify/reset_otp", methods=["GET", "POST"])
def verify_reset_otp():
    if "reset_user_id" not in session:
        flash("No pending password reset found.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(user_id=session["reset_user_id"]).first()

    if request.method == "POST":
        otp = request.form.get("otp")

        if not user:
            session.pop("pending_email", None)
            flash("User not found.", "error")
            return redirect(url_for("auth.forgot_password"))

        message, category = verify_otp(
            user.user_id,
            otp,
            "password-reset"
        )

        if category == "success":
            session["allow_password_reset"] = True
            return redirect(url_for("verify.reset_password"))

        flash(message, category)

    record = OTP.query.filter_by(
        u_id=user.user_id,
        purpose="password-reset"
    ).first()

    expired = False

    if record and record.expires_at <= datetime.utcnow():
        expired = True

    return render_template(
        "auth/verify.html",
        email=user.email_id,
        expired=expired,
        resend_url=url_for("verify.send_reset_otp")
    )


# Reset Password
@verify_bp.route("/verify/reset_password", methods=["GET", "POST"])
def reset_password():
    if "reset_user_id" not in session:
        flash("No pending password reset found.", "error")
        return redirect(url_for("auth.forgot_password"))

    if "allow_password_reset" not in session:
        flash("Please verify the OTP first.", "error")
        return redirect(url_for("verify.verify_reset_otp"))
    
    

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("verify.reset_password"))

        user = db.session.get(
            User,
            session["reset_user_id"]
        )

        if not user:
            flash(
                "Unable to reset password. Please start again.",
                "error"
            )
            session.pop("reset_user_id", None)
            return redirect(url_for("auth.forgot_password"))

        user.pass_hash = generate_password_hash(password)

        db.session.commit()

        session.pop("reset_user_id", None)
        session.pop("allow_password_reset", None)

        flash(
            "Password reset successful. Please log in.",
            "success"
        )
        create_notification(
                user_id=user.user_id,
                title="Password Reset",
                message="Your password has been reset successfully.",
                notification_type="security"
            )
        audit_log_action("password-reset", "credential", user_id=user.user_id, username=user.username)

        return redirect(url_for("auth.login"))

    return render_template("auth/reset_pass.html")


#device verification
@verify_bp.route("/verify/device", methods=["GET", "POST"])
def verify_device():
    if "pending_user_id" not in session:
        flash("No pending device verification found.", "error")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["pending_user_id"])
    
    if request.method == "POST":
        otp = request.form.get("otp")

        if not user:
            flash("User not found.", "error")
            session.pop("pending_user_id", None)
            return redirect(url_for("auth.login"))

        message, category = verify_otp(
            user.user_id,
            otp,
            "device-verification"
        )

        if category == "success":

            # Generate trusted device token
            device_token = secrets.token_urlsafe(32)

            # Store only the hash in the database
            device_token_hash = hash_data(device_token)

            trusted_device = TrustedDevice(
                device_token_hash=device_token_hash,
                u_id=user.user_id, 
                last_used_at=datetime.utcnow()
            )

            db.session.add(trusted_device)
                     
            db.session.commit()
            create_notification(
                user_id=user.user_id,
                title="Device Verified",
                message="A new device has been verified for your account.",
                notification_type="security"
            )
            audit_log_action("device-verified", "credential", user_id=user.user_id, username=user.username)

            # Create login session
            session["user_id"] = user.user_id
            session["username"] = user.username
            session.pop("pending_user_id", None)

            flash(message, category)

            # Redirect and place original token in browser cookie
            if user.u_role == "admin":
                response = redirect(url_for("dash.admin_dash"))
            else:
                response = redirect(url_for("dash.user_dash"))

            response.set_cookie(
                f"device_token_{user.user_id}",
                device_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",              # <-- add this
                max_age=60 * 60 * 24 * 30
            )

            return response

        flash(message, category)

    record = OTP.query.filter_by(
        u_id=user.user_id,
        purpose="device-verification"
    ).first()

    expired = False

    if record and record.expires_at <= datetime.utcnow():
        expired = True

    return render_template(
        "auth/verify.html",
        email=user.email_id,
        expired=expired,
        resend_url=url_for("verify.resend_device_otp")
    )


# Resend Device Verification OTP
@verify_bp.route("/verify/device/resend", methods=["POST"])
def resend_device_otp():
    if "reset_user_id" not in session:
        flash("No pending verification found.", "error")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["pending_user_id"])

    message, category = send_resend_otp(
        session["pending_user_id"],
        purpose="device-verification"
    )
    create_notification(
                user_id=user.user_id,
                title="Device Verification",
                message="An OTP has been sent to your email for device verification.",
                notification_type="security"
            )
    audit_log_action("sent-device-verification-otp", "email-otp", user_id=session["pending_user_id"])

    flash(message, category)

    return redirect(url_for("verify.verify_device"))

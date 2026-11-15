from datetime import datetime, timedelta
import secrets
from flask import (Blueprint, render_template, redirect, url_for, flash, session, request)
from app.routes.auth.set_pass import SetPasswordForm
from app.routes.auth.set_pass import SetPasswordForm
from app.routes.user.notification import create_notification
from app.services.authenticator_service import (generate_secret,encrypt_secret,decrypt_secret,generate_provisioning_uri,verify_code)
from werkzeug.security import generate_password_hash
import qrcode
import io
import base64

from app import db
from app.models import User, OTP
from app.routes.admin.admin import admin_required, audit_log_action


admin_settings_bp = Blueprint('admin_settings', __name__)


# =========================================================
# SETTINGS PAGE
# =========================================================

@admin_settings_bp.route('/admin/settings')
def admin_settings():
    denied = admin_required()

    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_profile.admin_profile"))
    
    active_tab = request.args.get("tab", "personal")

    return render_template(
        "admin/admin_settings.html",
        user=user, active_tab=active_tab
    )


# =========================================================
# SET PASSWORD
# =========================================================
@admin_settings_bp.route('/admin/settings/set-password', methods=['GET', 'POST'])
def admin_set_password():
    denied = admin_required()

    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User account not found.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    form = SetPasswordForm()

    if form.validate_on_submit():

        password = form.password.data
        confirm_password = form.confirm_password.data

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("admin/admin_set_password.html", form=form)

        if user.pass_hash:
            flash("You already have a password.", "info")
            return redirect(url_for("admin_settings.admin_settings"))

        user.pass_hash = generate_password_hash(password)

        db.session.commit()

        audit_log_action(
            "set-password",
            "credential",
            user_id=user.user_id,
            username=user.username
        )

        create_notification(
            user_id=user.user_id,
            title="Password Set Successfully",
            message="A password has been added to your JIRFLUX account.",
            notification_type="security"
        )

        flash("New password has been set successfully.", "success")
        return redirect(url_for("admin_settings.admin_settings"))

    return render_template("admin/admin_set_password.html", form=form)



# =========================================================
# CHANGE PASSWORD
# =========================================================
@admin_settings_bp.route('/admin/settings/password', methods=['POST'])
def admin_change_password():
    denied = admin_required()
    if denied:
        return denied
    
    return redirect(url_for('verify.reset_password'))
    
    
# =========================================================
# ENABLE 2FA
# =========================================================

@admin_settings_bp.route('/admin/settings/2fa')
def admin_setup_2fa():
    denied = admin_required()

    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    # If 2FA is already enabled
    if user.two_factor_enabled:
        flash("Two-factor authentication is already enabled.", "info")
        return redirect(url_for("admin_settings.admin_settings"))

    # Generate new TOTP secret
    secret = generate_secret()

    # Generate provisioning URI
    uri = generate_provisioning_uri(
        secret,
        user.email_id,
        issuer_name="Jirflux"
    )

    # Generate QR code
    qr = qrcode.make(uri)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    qr_code = base64.b64encode(
        buffer.getvalue()
    ).decode()

    # Store secret temporarily in session
    session["encrypt_secret"] = secret

    return render_template(
        "admin/admin_setup_2fa.html",
        qr_code=qr_code,
        email=user.email_id,
        user=user
    )   
# =========================================================
# VERIFY 2FA
# =========================================================

@admin_settings_bp.route('/admin/settings/2fa/verify', methods=['POST'])
def admin_verify_2fa():

    denied = admin_required()

    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    code = request.form.get("code", "").strip()

    if not code:
        flash("Please enter the authenticator code.", "error")
        return redirect(url_for("admin_settings.admin_setup_2fa"))

    # Get the temporary secret generated during setup
    secret = session.get("encrypt_secret")

    if not secret:
        flash("2FA setup has not been started. Please try again.", "error")
        return redirect(url_for("admin_settings.admin_setup_2fa"))

    # Verify authenticator code against the temporary secret
    if not verify_code(secret, code):
        flash("Invalid authenticator code.", "error")
        return redirect(url_for("admin_settings.admin_setup_2fa"))

    # Enable 2FA only after successful verification, then persist the encrypted secret
    user.totp_secret = encrypt_secret(secret)
    user.two_factor_enabled = True

    try:
        db.session.commit()
        session.pop("encrypt_secret", None)

        flash(
            "Two-factor authentication enabled successfully.",
            "success"
        )

        return redirect(url_for("admin_settings.admin_settings"))

    except Exception:
        db.session.rollback()

        flash(
            "Something went wrong while enabling 2FA.",
            "error"
        )

        return redirect(url_for("admin_settings.admin_setup_2fa"))
    
    
# =========================================================
# DISABLE 2FA
# =========================================================

@admin_settings_bp.route('/admin/settings/2fa/disable', methods=['POST'])
def admin_disable_2fa():

    denied = admin_required()

    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    if not user.two_factor_enabled:
        flash("Two-factor authentication is already disabled.", "info")
        return redirect(url_for("admin_settings.admin_settings"))

    code = request.form.get("code", "").strip()

    if not code:
        flash("Please enter your authenticator code.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    encrypted_secret = user.totp_secret

    if not encrypted_secret:
        flash("Two-factor authentication data was not found.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    secret = decrypt_secret(encrypted_secret)

    if not verify_code(secret, code):
        flash("Invalid authenticator code.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    try:

        user.two_factor_enabled = False
        user.totp_secret = None

        db.session.commit()

        flash(
            "Two-factor authentication has been disabled.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Something went wrong while disabling 2FA.",
            "error"
        )

    return redirect(url_for("admin_settings.admin_settings"))



# =========================================================
# UPDATE NOTIFICATIONS
# =========================================================

@admin_settings_bp.route('/admin/settings/notifications', methods=['POST'])
def admin_update_notifications():
    denied = admin_required()

    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_settings.admin_settings"))

    # Checkboxes only appear in form data when checked
    user.email_notifications = 'email_notifications' in request.form
    user.push_notifications = 'push_notifications' in request.form
    user.due_date_reminders = 'due_date_reminders' in request.form
    user.mentions_comments = 'mentions_comments' in request.form
    user.team_updates = 'team_updates' in request.form
    user.weekly_summary = 'weekly_summary' in request.form

    try:
        db.session.commit()
        flash("Notification preferences updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Something went wrong while updating notifications.", "error")

    return redirect(url_for("admin_settings.admin_settings", tab="notifications"))
from flask import Blueprint, redirect, render_template, url_for, session, flash, request
from app import oauth
from app.models import TrustedDevice, User, OAuthIdentity
from werkzeug.security import check_password_hash
import secrets
from datetime import datetime, timedelta
from app import db

from app.routes.auth.google_link_form import GoogleLinkForm

from app.routes.user.notification import create_notification
from app.services.email_service import send_alert_email
from app.services.encryption_service import hash_data
from app.services.otp_service import send_resend_otp
from app.routes.admin.admin import audit_log_action

google_auth_bp = Blueprint("google_auth", __name__)



DEVICE_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def dashboard_redirect(user):
    target = "dash.admin_dash" if user.u_role == "admin" else "dash.user_dash"
    return redirect(url_for(target))


def start_session(user):
    session["user_id"] = user.user_id
    session["username"] = user.username


def trust_this_device(user, response):
    """Create a TrustedDevice row and set the device cookie on the response."""
    token = secrets.token_urlsafe(32)

    db.session.add(TrustedDevice(
        u_id=user.user_id,
        device_token_hash=hash_data(token),
        last_used_at=datetime.utcnow(),
    ))
    db.session.commit()

    response.set_cookie(
        f"device_token_{user.user_id}",
        token,
        httponly=True,
        secure=False,          # set True in production (HTTPS)
        samesite="Lax",
        max_age=DEVICE_COOKIE_MAX_AGE,
    )
    return response


def generate_google_username(email):
    base_username = email.split("@")[0].strip().lower()
    base_username = base_username[:45]

    username = base_username
    counter = 1

    while User.query.filter_by(username=username).first():
        suffix = str(counter)
        username = f"{base_username[:50 - len(suffix)]}{suffix}"
        counter += 1

    return username


@google_auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for(
        "google_auth.google_callback",
        _external=True
    )
    session["google_auth_action"] = "login" 

    return oauth.google.authorize_redirect(redirect_uri)


@google_auth_bp.route("/register/google")
def google_register():

    session["google_auth_action"] = "register"

    redirect_uri = url_for(
        "google_auth.google_callback",
        _external=True
    )
    return oauth.google.authorize_redirect(redirect_uri)

@google_auth_bp.route("/login/google/callback")
def google_callback():
    auth_action = session.pop("google_auth_action", "login")

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            flash("Unable to verify your Google account.", "error")
            return redirect(url_for("auth.login"))

        google_sub = user_info.get("sub")
        google_email = user_info.get("email")

        if not google_sub or not google_email or user_info.get("email_verified") is not True:
            flash("Google account verification failed.", "error")
            return redirect(url_for("auth.login"))

        normalized_email = google_email.strip().lower()

        identity = OAuthIdentity.query.filter_by(
            provider="google",
            provider_user_id=google_sub
        ).first()

        # ---------------------------------------------------------
        # REGISTER
        # ---------------------------------------------------------
        if auth_action == "register":
            if identity:
                flash("This Google account is already registered. Please log in.", "info")
                return redirect(url_for("auth.login"))

            if User.query.filter_by(email_id=normalized_email).first():
                flash("An account with this email already exists. Please use Google Login.", "info")
                return redirect(url_for("auth.login"))

            username = generate_google_username(normalized_email)
            full_name = user_info.get("name") or username

            new_user = User(
                username=username,
                full_name=full_name[:50],
                email_id=normalized_email,
                pass_hash=None,
                verified=True,
                picture=user_info.get("picture"),
            )
            db.session.add(new_user)
            db.session.flush()

            db.session.add(OAuthIdentity(
                user_id=new_user.user_id,
                provider="google",
                provider_user_id=google_sub,
                provider_email=normalized_email,
            ))
            db.session.commit()

            audit_log_action("google-registration", "oauth",
                             user_id=new_user.user_id, username=new_user.username)
            create_notification(
                user_id=new_user.user_id,
                title="Google Registration Successful",
                message="Your JIRFLUX account was created using Google.",
                notification_type="security",
            )

            start_session(new_user)
            flash("Account created successfully with Google!", "success")

            # The user just signed up from this browser, so trust it (no alert)
            return trust_this_device(new_user, dashboard_redirect(new_user))

        # ---------------------------------------------------------
        # LOGIN: link by verified email if no identity yet
        # ---------------------------------------------------------
        if not identity:
            existing_user = User.query.filter_by(email_id=normalized_email).first()

            if not existing_user:
                flash("No JIRFLUX account found with this email. Please register first.", "error")
                return redirect(url_for("auth.login"))

            if OAuthIdentity.query.filter_by(user_id=existing_user.user_id, provider="google").first():
                flash("A different Google account is already linked to this JIRFLUX account.", "error")
                return redirect(url_for("auth.login"))

            existing_user.verified = True
            identity = OAuthIdentity(
                user_id=existing_user.user_id,
                provider="google",
                provider_user_id=google_sub,
                provider_email=normalized_email,
            )
            db.session.add(identity)
            db.session.commit()

            audit_log_action("google-account-linked", "oauth",
                             user_id=existing_user.user_id, username=existing_user.username)
            create_notification(
                user_id=existing_user.user_id,
                title="Google Account Linked",
                message="Your Google account was automatically linked using Google's verified email.",
                notification_type="security",
            )

        user = db.session.get(User, identity.user_id)

        if not user:
            flash("Associated JIRFLUX account was not found.", "error")
            return redirect(url_for("auth.login"))

        if normalized_email != user.email_id.strip().lower():
            flash("Your Google email does not match your JIRFLUX account email.", "error")
            return redirect(url_for("auth.login"))

        # ---------------------------------------------------------
        # Account lock
        # ---------------------------------------------------------
        now = datetime.utcnow()

        if user.account_lock_until:
            if now < user.account_lock_until:
                flash("Your account is temporarily locked. Please try again later.", "error")
                return redirect(url_for("auth.login"))

            user.account_lock_until = None
            user.password_attempt = 0
            db.session.commit()

        # ---------------------------------------------------------
        # Trusted device -> log in directly
        # ---------------------------------------------------------
        device_token = request.cookies.get(f"device_token_{user.user_id}")
        trusted_device = None

        if device_token:
            trusted_device = TrustedDevice.query.filter_by(
                u_id=user.user_id,
                device_token_hash=hash_data(device_token),
            ).first()

        if trusted_device:
            trusted_device.last_used_at = now
            db.session.commit()

            start_session(user)
            audit_log_action("login", "credential",
                             user_id=user.user_id, username=user.username)
            flash("Google Login Successful!", "success")
            return dashboard_redirect(user)

        # ---------------------------------------------------------
        # Unknown device + 2FA on -> OTP device verification
        # ---------------------------------------------------------
        if user.two_factor_enabled:
            session["pending_user_id"] = user.user_id

            send_alert_email(user.email_id)
            audit_log_action("unauthorized-device-login", "credential",
                             user_id=user.user_id, username=user.username)
            create_notification(
                user_id=user.user_id,
                title="Unauthorized Device Login",
                message="A new device attempted to log in to your account.",
                notification_type="security",
            )

            send_resend_otp(user.user_id, purpose="device-verification")
            audit_log_action("device-verification-email", "email-otp",
                             user_id=user.user_id, username=user.username)
            create_notification(
                user_id=user.user_id,
                title="Device Verification Email Sent",
                message="A device verification OTP has been sent to your email.",
                notification_type="security",
            )

            return redirect(url_for("verify.verify_device"))

        # ---------------------------------------------------------
        # Unknown device + 2FA off -> alert once, log in, trust device
        # ---------------------------------------------------------
        send_alert_email(user.email_id)
        audit_log_action("unauthorized-device-login", "credential",
                         user_id=user.user_id, username=user.username)
        audit_log_action("sent-alert-email", "email",
                         user_id=user.user_id, username=user.username)
        create_notification(
            user_id=user.user_id,
            title="New Device Login",
            message="Your account was accessed from a new, unrecognized device.",
            notification_type="security",
        )

        start_session(user)
        audit_log_action("login", "credential",
                         user_id=user.user_id, username=user.username)
        flash("Google Login Successful!", "success")

        return trust_this_device(user, dashboard_redirect(user))

    except Exception:
        import traceback
        db.session.rollback()
        print("GOOGLE LOGIN ERROR:")
        traceback.print_exc()

        flash("Google Sign-In failed. Please try again.", "error")
        return redirect(url_for("auth.login"))
 
@google_auth_bp.route("/google/confirm-link", methods=["GET", "POST"])
def confirm_google_link():

    form = GoogleLinkForm()
    
    # Check pending Google linking information
    pending_user_id = session.get("pending_google_link_user_id")
    google_sub = session.get("pending_google_sub")
    google_email = session.get("pending_google_email")

    if not pending_user_id or not google_sub or not google_email:
        flash("No pending Google account linking request.", "error")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, pending_user_id)

    if not user:
        session.pop("pending_google_link_user_id", None)
        session.pop("pending_google_sub", None)
        session.pop("pending_google_email", None)

        flash("JIRFLUX account not found.", "error")
        return redirect(url_for("auth.login"))

    if (
        user.email_id.strip().lower() != google_email
        or not user.verified
    ):
        flash("Account verification failed.", "error")
        return redirect(url_for("auth.login"))

    # Check whether this Google identity is already linked
    existing_identity = OAuthIdentity.query.filter_by(
        provider="google",
        provider_user_id=google_sub
    ).first()

    if existing_identity:
        flash("This Google account is already linked.", "error")
        return redirect(url_for("auth.login"))
    
    linked_identity = OAuthIdentity.query.filter_by(
        user_id=user.user_id,
        provider="google"
    ).first()

    if linked_identity:
        flash(
            "A Google account is already linked to your JirFlux account.",
            "error"
        )
        return redirect(url_for("auth.login"))
    
    # GET request: display confirmation page
    if request.method == "GET":
        return render_template(
            "auth/confirm_google_link.html",
            form=form
        )

    # POST request: verify existing JirFlux password
    now = datetime.utcnow()

    if user.account_lock_until:
        if now < user.account_lock_until:
            flash(
                "Your account is temporarily locked. Please try again later.",
                "error"
            )
            return render_template("auth/confirm_google_link.html", form=form)

        user.account_lock_until = None
        user.password_attempt = 0
        
        db.session.commit()
   

    if not form.validate_on_submit():

        return render_template(
            "auth/confirm_google_link.html",
            form=form
        )

    password = request.form.get("password", "")

    # Google-only accounts may not have a password
    if not user.pass_hash:
        flash(
            "This account does not have a password. Please use your existing account recovery process first.",
            "error"
        )
        return render_template("auth/confirm_google_link.html", form=form)

    
    if not check_password_hash(user.pass_hash, password):

        user.password_attempt += 1

        create_notification(
            user_id=user.user_id,
            title="Google Linking Failed",
            message="An incorrect password was entered while linking a Google account.",
            notification_type="security"
        )

        if user.password_attempt >= 5:
            user.account_lock_until = now + timedelta(days=1)

            audit_log_action(
                "account_locked",
                "credential",
                user_id=user.user_id,
                username=user.username
            )

        db.session.commit()

        audit_log_action(
            "google-link-failed",
            "credential",
            user_id=user.user_id,
            username=user.username
        )

        flash("Incorrect password.", "error")
        return render_template("auth/confirm_google_link.html", form=form)

    # Password verified: create Google identity
    new_identity = OAuthIdentity(
        user_id=user.user_id,
        provider="google",
        provider_user_id=google_sub,
        provider_email=google_email
    )

    db.session.add(new_identity)


    try:
        db.session.commit()

        audit_log_action(
            "google-account-linked",
            "oauth",
            user_id=user.user_id,
            username=user.username
        )

        create_notification(
            user_id=user.user_id,
            title="Google Account Linked",
            message="Your Google account has been successfully linked to JIRFLUX.",
            notification_type="security"
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    # Clear temporary Google linking information
    session.pop("pending_google_link_user_id", None)
    session.pop("pending_google_sub", None)
    session.pop("pending_google_email", None)

    flash(
        "Google account linked successfully! You can now sign in with Google.",
        "success"
    )

    return redirect(url_for("auth.login"))

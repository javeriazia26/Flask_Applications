# Authorization Routes
from datetime import date, datetime, timedelta
import secrets
from urllib import response

from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from app import db
from app.models import User, TrustedDevice
from app.routes.auth.forget_pass import ForgetPasswordForm
from app.routes.auth.reg_form import RegistrationForm
from app.routes.auth.login_form import loginForm
from app.routes.admin.admin import audit_log_action
from werkzeug.security import check_password_hash, generate_password_hash

from app.routes.user.notification import create_notification
from app.services.email_service import send_alert_email
from app.services.encryption_service import hash_data
from app.services.otp_service import send_resend_otp


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        hashed_password = generate_password_hash(password)

        #check user exists or not
        existing_user = User.query.filter(
            (User.username == username) | (User.email_id == email)
        ).first()
        if existing_user:
            flash("User already Exists", "info")
            return redirect(url_for('auth.register'))

        #add user if not not exists
        user = User(
            username=username,
            full_name=username,
            email_id=email,
            pass_hash=hashed_password,
        )

        db.session.add(user)
        db.session.commit()

        message, category = send_resend_otp(user.user_id, purpose="email-verification")
        audit_log_action("register", "credential", user_id=user.user_id, username=username)
        audit_log_action("sent-email-verification", "email-otp", user_id=user.user_id, username=username)
        create_notification(
            user_id=user.user_id,
            title="Login Failed",
            message="Your login attempt has failed.",
            notification_type="security"
        )

        if category == "warning":
            flash(message, category)

        session['pending_user_id'] = user.user_id

        flash("Registered Successfully", "success")
        return redirect(url_for('verify.verify'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    form = loginForm()
    print("ALL COOKIES ON THIS REQUEST:", dict(request.cookies))

    now = datetime.utcnow()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data


        #check user exists
        user = User.query.filter_by(email_id=email).first()

        if user and user.account_lock_until:
            if now < user.account_lock_until:
                flash(
                    "Your account is temporarily locked. Please try again later.",
                    "error"
                )
                create_notification(
                    user_id=user.user_id,
                    title="Account Temporarily Locked",
                    message="Your account has been temporarily locked after multiple failed login attempts.",
                    notification_type="security"
                )
                return render_template("auth/login.html", form=form)

            # 1-day lock has expired
            user.account_lock_until = None
            user.password_attempt = 0
            db.session.commit()

        # -------------------------------------------------
        # Password check runs for EVERY user, not just
        # ones who previously had a lock on their account
        # -------------------------------------------------
        if user and check_password_hash(user.pass_hash, password):

            if not user.verified:
                session['pending_user_id'] = user.user_id
                message, category = send_resend_otp(user.user_id, purpose="email-verification")
                audit_log_action("sent-email-verification", "email-otp", user_id=user.user_id, username=user.username)

                flash(message, category)

                create_notification(
                    user_id=user.user_id,
                    title="Registered Successfully",
                    message="Welcome to jirflux! Your account has been created successfully.",
                    notification_type="register"
                )
                return redirect(url_for('verify.verify'))

            # -------------------------------------------------
            # Check trusted device FIRST, regardless of 2FA
            # -------------------------------------------------
            cookie_name = f"device_token_{user.user_id}"
            # f"device_token_{user.user_id}"

            device_token = request.cookies.get(cookie_name)
            
            
            trusted_device = None
            
            if device_token:
                device_token_hash = hash_data(device_token)
        

                trusted_device = TrustedDevice.query.filter_by(
                    u_id=user.user_id,
                    device_token_hash=device_token_hash
                ).first()
                
            if trusted_device:
                # Known device -> log in directly, no matter if 2FA is on
                trusted_device.last_used_at = now
                session['user_id'] = user.user_id
                session['username'] = user.username
                db.session.commit()

                audit_log_action("login", "credential", user_id=user.user_id, username=user.username)


                flash("Login Successful!", "success")
                if user.u_role == "admin":
                    response = redirect(url_for("dash.admin_dash"))
                else:
                    response = redirect(url_for("dash.user_dash"))

                response.set_cookie(
                    cookie_name,
                    device_token,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=60 * 60 * 24 * 30,
                )

                return response

            # -------------------------------------------------
            # Untrusted / unknown device from here on
            # -------------------------------------------------
            if user.two_factor_enabled:
                if not trusted_device:
                    
                    session['pending_user_id'] = user.user_id

                    # message, category = send_alert_email(user.email_id)

                    audit_log_action("unauthorized-device-login", "credential", user_id=user.user_id, username=user.username)
                    audit_log_action("sent-alert-email", "email", user_id=user.user_id, username=user.username)
                    create_notification(
                            user_id=user.user_id,
                            title="Unauthorized Device Login",
                            message="An unauthorized device attempted to log in to your account.",
                            notification_type="security"
                        )

                    message, category = send_resend_otp(user.user_id, purpose="device-verification")
                    create_notification(
                            user_id=user.user_id,
                            title="Device Verification Email Sent",
                            message="We have sent a device verification email to authorize your new device. Please check your email and spam folder too.",
                            notification_type="security"
                        )

                    audit_log_action("device-verification-email", "email-otp", user_id=user.user_id, username=user.username)
                    return redirect(url_for('verify.verify_device'))
                
                if trusted_device:
                    # Known device -> log in directly, no matter if 2FA is on
                    trusted_device.last_used_at = now
                    session['user_id'] = user.user_id
                    session['username'] = user.username
                    db.session.commit()

                    audit_log_action("login", "credential", user_id=user.user_id, username=user.username)

                    flash("Login Successful!", "success")
                    if user.u_role == "admin":
                        response = redirect(url_for("dash.admin_dash"))
                    else:
                        response = redirect(url_for("dash.user_dash"))

                    response.set_cookie(
                        cookie_name,
                        device_token,
                        httponly=True,
                        secure=False,
                        samesite="Lax",
                        max_age=60 * 60 * 24 * 30,
                    )

                    return response

            else:
                session['user_id'] = user.user_id
                session['username'] = user.username
                # message, category = send_alert_email(user.email_id)
                
                if not trusted_device:
                    cookie_name = f"device_token_{user.user_id}"
                    device_token = secrets.token_urlsafe(32)
                    # Store only the hash in the database
                    device_token_hash = hash_data(device_token)
                    audit_log_action("unauthorized-device-login", "credential", user_id=user.user_id, username=user.username)
                    audit_log_action("sent-alert-email", "email", user_id=user.user_id, username=user.username)
                    create_notification(
                            user_id=user.user_id,
                            title="Unauthorized Device Login",
                            message="An unauthorized device attempted to log in to your account.",
                            notification_type="security"
                        )

                    flash("Login Successful!", "success")
                    if user.u_role == "admin":
                        response = redirect(url_for("dash.admin_dash"))
                    else:
                        response = redirect(url_for("dash.user_dash"))

                    response.set_cookie(
                        cookie_name,
                        device_token,
                        httponly=True,
                        secure=False,
                        samesite="Lax",
                        max_age=60 * 60 * 24 * 30,
                    )

                    return response

        if user:
            # Count failed password attempt
            user.password_attempt += 1
            create_notification(
                user_id=user.user_id,
                title="Login Failed",
                message="Your login attempt has failed.",
                notification_type="security"
            )
            flash("Invalid username or password", "error")
            if user.password_attempt >= 5:
                user.account_lock_until = now + timedelta(days=1)
                audit_log_action("account_locked", "credential", user_id=user.user_id, username=user.username)

            db.session.commit()

            audit_log_action("login_failed", "credential", user_id=user.user_id, username=user.username)
        else:
            flash("Invalid username or password", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    username = session.get('username')

    session.clear()

    audit_log_action("logout", "credential", user_id=user_id, username=username)
    
    response = redirect(url_for('auth.login'))
    response.delete_cookie('session', path='/')   # force the browser to drop it
    return response


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgetPasswordForm()
    
    if form.validate_on_submit():
        submitted_email = form.email.data
        user = User.query.filter_by(email_id=submitted_email).first()
        
        session["reset_user_id"] = user.user_id
        

        if user:
            message, category = send_resend_otp(user.user_id, purpose="password-reset")
            audit_log_action("forgot_password", "otp_requested", user_id=user.user_id, username=user.username)

            flash(message, category)
            create_notification(
                user_id=user.user_id,
                title="Password Reset Requested",
                message="A password reset request has been initiated for this email address.",
                notification_type="security"
            )
            return redirect(url_for("verify.verify_reset_otp"))

        flash("We've sent a password reset code. Please check your email.", "info")
        return render_template("auth/verify.html", form=form, email=submitted_email)

    return render_template("auth/forgot_pass.html", form=form)


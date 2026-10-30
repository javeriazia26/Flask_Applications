#Authorization Routes
from datetime import datetime
from email.mime import message
from unicodedata import category

from flask import Blueprint, render_template, redirect, url_for, flash, session
from app import db
from app.models import Credential
from app.routes.forget_pass import ForgetPasswordForm
from app.routes.reg_form import RegistrationForm
from app.routes.login_form import loginForm
from werkzeug.security import check_password_hash, generate_password_hash

from app.services.email_service import send_verification_email
from app.services.otp_service import create_otp, send_resend_otp
from app.routes.admin.admin import log_action

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data           
        email = form.email.data
        password = form.password.data
        
        hashed_password=generate_password_hash(password)
        #check user exists or not
        existing_user = Credential.query.filter((Credential.username==username) | (Credential.email==email)).first()
        if existing_user:
            flash("User already Exists", "info")
            return redirect(url_for('auth.register'))
    
    #add user if not not exists
        user=Credential(username=username, email=email, hashed_password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        message, category = send_resend_otp(user.id, purpose="email-verification")

        if category == "warning":
            flash(message, category)
    
        session['pending_user_id']=user.id
        log_action("register", "credential", user_id=user.id, username=username)
        flash("Registered Successfully", "success")
        return redirect(url_for('verify.verify'))
        
    return render_template('auth/register.html', form=form)


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():          
        email = form.email.data
        password = form.password.data
        #check user exists
        user = Credential.query.filter_by(email=email).first()

        if user and check_password_hash(user.hashed_password, password):
            
            if not user.verified:
                session['pending_user_id'] = user.id
                message, category = send_resend_otp(user.id,purpose="email-verification")
                
                flash(message, category)
                return redirect(url_for('verify.verify'))
            
            session['user_id']=user.id
            session['username'] = user.username
            log_action("login", "credential", user_id=user.id, username=user.username)
            if user.role == "admin":
                flash("Login Successful!", "success")
                return redirect(url_for('dash.admin_dash'))
            else: 
                flash("Login Successful!", "success")
                return redirect(url_for('dash.user_dash'))
        else:
            log_action("login_failed", "credential", username=email)
            flash("login failed", "error")
            flash("Invalid username or password", "error")
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    username = session.get('username')

    session.pop('user_id', None)
    session.pop('username', None)
    log_action("logout", "credential", user_id=user_id, username=username)
    flash("Logout Successfully!", "success")
    return redirect(url_for('auth.login'))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    form = ForgetPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        user = Credential.query.filter_by(email=email).first()

        if user:
            session["reset_user_id"] = user.id
            message, category = send_resend_otp(user.id,purpose="password-reset")

            flash(message, category)
            return redirect(url_for("verify.verify_reset_otp"))
        
        flash("We've sent a password reset code. Please check your email.", "info")
        return redirect(url_for("verify.verify_reset_otp"))

    return render_template("forgot_pass.html", form=form)
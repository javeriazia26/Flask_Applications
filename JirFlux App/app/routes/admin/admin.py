from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User, AuditLog
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required():
    """
    Call this at the top of every admin route.
    Returns None if user is admin, otherwise returns a redirect.
    """
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(user_id=session['user_id']).first()
    
    if user.u_role != "admin":
        flash("Access denied!", "error")
        return redirect(url_for('dash.user_dash'))
    
    return None


def audit_log_action(action, entity, user_id=None, username=None):
    try:
        new_log = AuditLog(
            date     = datetime.now().date(),
            time     = datetime.now().time(),
            username = username or session.get('username'),
            action   = action,
            entity   = entity,
            u_id     = user_id if user_id is not None else session.get('user_id')
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        # if logging fails, don't crash the whole app
        db.session.rollback()
        print(f"Audit log error: {e}")

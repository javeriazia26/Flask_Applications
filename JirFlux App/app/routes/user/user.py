from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User, ItemLog, Project
from datetime import datetime


user_bp = Blueprint('user', __name__)

def user_required():
    """
    Call this at the top of every user route.
    Returns None if user is logged in, otherwise returns a redirect.
    """
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(user_id=session['user_id']).first()
    
    if user.u_role != "user":
        flash("Access denied!", "error")
        return redirect(url_for('auth.login'))
    
    return None



def log_action(action, w_title, p_id, w_id, user_id=None, username=None, project=None):
    try:
        new_log = ItemLog(
            date     = datetime.now().date(),
            time     = datetime.now().time(),
            username = username or session.get('username'),
            action   = action,
            project   = project or session.get('p_title'),
            p_id = p_id or session.get('p_id'),
            w_id = w_id or session.get('w_id'),
            u_id     = user_id if user_id is not None else session.get('user_id'),
            w_title     = w_title
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        # if logging fails, don't crash the whole app
        db.session.rollback()
        print(f"Item log error: {e}")

#log_action('created', work_item_id, project=project.p_title, user_id=assignee.u_id, username=assignee.u_name)
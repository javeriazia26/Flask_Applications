from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import AuditLog, User, WorkItem, ItemLog
from datetime import date, datetime

from app.routes.admin.admin import admin_required
from app.routes.admin.admin import audit_log_action


dash_bp = Blueprint('dash', __name__)


@dash_bp.route('/user_dash')
def user_dash():
    if "user_id" not in session:
        flash("Access denied!", "error")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(user_id=session['user_id']).first()
    if user.u_role != "user":
        flash("Access denied!", "error")
        return redirect(url_for('dash.user_dash'))

    today = date.today()
    user_id = session['user_id']

    completed_count = WorkItem.query.filter_by(u_id=user_id, progress="completed").count()
    in_progress_count = WorkItem.query.filter_by(u_id=user_id, progress="in-progress").count()
    not_started_count = WorkItem.query.filter_by(u_id=user_id, progress="not-started").count()
    due_today_count = WorkItem.query.filter_by(u_id=user_id, deadline=today).count()

    overdue_count = (
        WorkItem.query
        .filter(
            WorkItem.u_id == user_id,
            WorkItem.deadline < today,
            WorkItem.progress != "completed",
        )
        .count()
    )

    # ItemLog.w_id -> WorkItem.work_item_id (not "item_id" — that column
    # doesn't exist on WorkItem). ItemLog already carries denormalized
    # `project` and `username` strings, so no extra join/relationship
    # is needed to display them.
    item_logs = (
        ItemLog.query
        .join(WorkItem, ItemLog.w_id == WorkItem.work_item_id)
        .filter(WorkItem.u_id == user_id)
        .order_by(ItemLog.date.desc(), ItemLog.time.desc())
        .limit(10)
        .all()
    )

    total_count = completed_count + in_progress_count + not_started_count
    completion_rate = round((completed_count / total_count) * 100) if total_count else 0

    return render_template(
        'user/user_dash.html',
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        not_started_count=not_started_count,
        due_today_count=due_today_count,
        overdue_count=overdue_count,
        completion_rate=completion_rate,
        item_logs=item_logs,
        today=today,
        user=user,
        active_page='dashboard',
    )


@dash_bp.route('/board')
def board():
    if "user_id" not in session:
        flash("Access denied!", "error")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(user_id=session['user_id']).first()
    if user.u_role != "user":
        flash("Access denied!", "error")
        return redirect(url_for('dash.user_dash'))

    user_id = session['user_id']

    all_items = WorkItem.query.filter_by(u_id=user_id).order_by(WorkItem.deadline.asc()).all()

    not_started_items = [i for i in all_items if i.progress == "not-started"]
    in_progress_items = [i for i in all_items if i.progress == "in-progress"]
    completed_items = [i for i in all_items if i.progress == "completed"]

    return render_template(
        'user/board.html',
        not_started_items=not_started_items,
        in_progress_items=in_progress_items,
        completed_items=completed_items,
        user=user,
        active_page='board',
    )

@dash_bp.route('/admin_dash')
def admin_dash():
    denied = admin_required()
    if denied:
        return denied

    user = User.query.get(session["user_id"])

    audit_log_action = AuditLog.query.order_by(AuditLog.date.desc(), 
                AuditLog.time.desc()).limit(10).all()
    
    return render_template('admin/admin_dash.html', 
        all_audit_logs=audit_log_action,       
        )
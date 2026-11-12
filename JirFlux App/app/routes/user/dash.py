from sqlalchemy import or_, text

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, request
from app import db
from app.models import Assignee, AuditLog, Project, ProjectMember, User, WorkItem, ItemLog
from datetime import date, datetime

from app.routes.admin import audit_log
from app.routes.admin.admin import admin_required
from app.routes.user.user import user_required


dash_bp = Blueprint('dash', __name__)


STATUS_MAP = {
    "not-started": "Not Started",
    "in-progress": "In Progress",
    "completed":   "Completed",
}
DB_TO_KEY = {v: k for k, v in STATUS_MAP.items()}


@dash_bp.route('/user_dash')
def user_dash():
    denied = user_required()
    if denied:
        return denied
    
    user = User.query.filter_by(user_id=session['user_id']).first()
    
    today = date.today()
    user_id = session['user_id']
    counts = db.session.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE w.progress = 'Completed')                        AS completed,
            COUNT(*) FILTER (WHERE w.progress = 'In Progress')                      AS in_progress,
            COUNT(*) FILTER (WHERE w.progress = 'Not Started')                      AS not_started,
            COUNT(*) FILTER (WHERE w.deadline = :today)                             AS due_today,
            COUNT(*) FILTER (WHERE w.deadline < :today AND w.progress != 'Completed') AS overdue
        FROM work_items w
        WHERE w.u_id = :user_id
        OR EXISTS (
                SELECT 1 FROM assignees a
                WHERE a.w_id = w.work_item_id AND a.u_id = :user_id
        )
    """), {"user_id": user_id, "today": today}).one()

    completed_count   = counts.completed
    in_progress_count = counts.in_progress
    not_started_count = counts.not_started
    due_today_count   = counts.due_today
    overdue_count     = counts.overdue

    item_logs = visible_logs(user_id, 10)        # small panel
    all_item_logs = visible_logs(user_id, 200)   # full window

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
        all_item_logs=all_item_logs,
        today=today,
        user=user,
        active_page='dashboard',
    )


def visible_logs(user_id, limit):
    return db.session.execute(text("""
        SELECT i.date, i.time, i.username, i.w_title, i.project, i.action
        FROM item_log i
        JOIN projects p ON p.project_id = i.p_id
        WHERE p.u_id = :user_id
           OR EXISTS (
                SELECT 1 FROM project_member pm
                WHERE pm.p_id = i.p_id AND pm.user_id = :user_id
           )
        ORDER BY i.date DESC, i.time DESC
        LIMIT :limit
    """), {"user_id": user_id, "limit": limit}).fetchall()

@dash_bp.route('/admin_dash')
def admin_dash():
    denied = admin_required()
    if denied:
        return denied
    
    user = User.query.filter_by(user_id=session['user_id']).first()

    audit_log =  AuditLog.query.order_by(AuditLog.date.desc(), AuditLog.time.desc()).limit(10).all()
    return render_template('admin/admin_dash.html',
        user=user,                   
        audit_logs=audit_log,
        active_page='dashboard')



@dash_bp.route('/board')
def board():
    
    denied = user_required()
    if denied:
        return denied

    uid = session['user_id']
    user = User.query.filter_by(user_id=uid).first()

    # ids of work items assigned to me
    assigned_ids = db.session.query(Assignee.w_id).filter(Assignee.u_id == uid)
    
    rows = (
        db.session.query(WorkItem, Project.p_title)
        .join(Project, Project.project_id == WorkItem.p_id)
        .filter(db.or_(
            WorkItem.u_id == uid,                    # created by me
            WorkItem.work_item_id.in_(assigned_ids)  # assigned to me
        ))
        .order_by(WorkItem.deadline.asc().nulls_last())
        .all()
    )

    columns = {key: [] for key in STATUS_MAP}
    for item, project_name in rows:
        item.project_name = project_name or "No project"
        key = DB_TO_KEY.get(item.progress)
        if key:
            columns[key].append(item)

    return render_template(
        'user/board.html',
        not_started_items=columns["not-started"],
        in_progress_items=columns["in-progress"],
        completed_items=columns["completed"],
        user=user,
        active_page='board',
    )


@dash_bp.route('/board/move', methods=['POST'])
def board_move():
    if "user_id" not in session:
        return jsonify(ok=False, error="Not logged in"), 401

    data = request.get_json(silent=True) or {}
    new_status = STATUS_MAP.get(data.get("status"))
    if not new_status:
        return jsonify(ok=False, error="Invalid status"), 400

    # Filtering by u_id means users can only move their own items
    item = WorkItem.query.filter_by(
        work_item_id=data.get("item_id"), u_id=session['user_id']
    ).first()
    if not item:
        return jsonify(ok=False, error="Item not found"), 404

    item.progress = new_status
    db.session.commit()
    return jsonify(ok=True)
from datetime import date

from flask import Blueprint, render_template, session, request
from flask_login import current_user
from sqlalchemy import text
from app import db
import app.models
from app.routes.user.user import user_required

task_bp = Blueprint('task', __name__)

today = date.today()

STATUS_OPTIONS = ['Not Started', 'In Progress', 'Completed']


# Display all tasks related to the logged-in user, with status/priority
# filtering and sorting applied together in a single query.
@task_bp.route('/project/<int:p_id>/tasks')
def task():

    # Check whether user is logged in
    denied = user_required()
    if denied:
        return denied

    # Get logged-in user
    user = app.models.User.query.filter_by(user_id=session["user_id"]).first()

    selected_status = request.args.get('status', 'All')
    selected_priority = request.args.get('priority')
    selected_sort = request.args.get('sort', 'priority')

    base_query = app.models.WorkItem.query.filter_by(u_id=user.user_id)
    # --- Counts per status tab (computed before the status filter itself) ---
    status_counts = {
        status: base_query.filter(app.models.WorkItem.progress == status).count()
        for status in STATUS_OPTIONS
    }
    status_counts['All'] = base_query.count()

    # --- Build the filtered + sorted work item query ---
    query = base_query

    if selected_status != 'All':
        query = query.filter(app.models.WorkItem.progress == selected_status)

    if selected_priority:
        query = query.filter(app.models.WorkItem.priority == selected_priority)

    sort_columns = {
        'priority': app.models.WorkItem.priority,
        'deadline': app.models.WorkItem.deadline,
        'title': app.models.WorkItem.w_title,
    }
    sort_column = sort_columns.get(selected_sort, app.models.WorkItem.priority)
    query = query.order_by(sort_column.asc())

    work_items = query.filter_by(u_id=user.user_id).all()

    # --- Assignees for work items the user owns or is assigned to ---
    query = text("""
        SELECT w.w_title, w.priority, w.progress, w.start_date, w.deadline,
            a.u_id, u.full_name, u.username
        FROM work_items w
            LEFT JOIN assignees a
            ON w.work_item_id = a.w_id
            LEFT JOIN users u
            ON u.user_id = a.u_id          -- FK: assignees.u_id -> users.user_id
        WHERE w.u_id = :user_id OR a.u_id = :user_id;
    """)

    result = db.session.execute(
        query,
        {"user_id": session["user_id"]}
    )
    assignees = result.fetchall()

    sort_options = {
        'priority': 'Priority',
        'deadline': 'Deadline',
        'title': 'Title'
    }
    filter_options = {
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low'
    }

    return render_template(
        'user/project.html',
        work_items=work_items,
        user=current_user,
        assignees=assignees,
        selected_status=selected_status,
        selected_priority=selected_priority,
        selected_sort=selected_sort,
        status_counts=status_counts,
        sort_options=sort_options,
        filter_options=filter_options,
        today=today
    )

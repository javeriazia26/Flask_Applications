from datetime import date

from flask import Blueprint, render_template, session, request
from flask_login import current_user
from sqlalchemy import text, bindparam, or_

from app import db
import app.models
from app.routes.user.user import user_required

task_bp = Blueprint('task', __name__)

today = date.today()

STATUS_OPTIONS = ['Not Started', 'In Progress', 'Completed']


# Display all tasks related to the logged-in user, with status/priority
# filtering and sorting applied together in a single query.
@task_bp.route('/tasks')
def task():
    denied = user_required()
    if denied:
        return denied

    user = app.models.User.query.filter_by(user_id=session["user_id"]).first()
    WorkItem = app.models.WorkItem

    selected_status = request.args.get('status', 'All')
    selected_priority = request.args.get('priority')
    selected_sort = request.args.get('sort', 'priority')

    # ids of work items where this user is an assignee
    assigned_ids = [r[0] for r in db.session.execute(
        text("SELECT w_id FROM assignees WHERE u_id = :uid"),
        {"uid": user.user_id}
    )]

    # owner OR assignee
    base_query = WorkItem.query.filter(
        or_(WorkItem.u_id == user.user_id, WorkItem.work_item_id.in_(assigned_ids))
    )

    status_counts = {
        s: base_query.filter(WorkItem.progress == s).count() for s in STATUS_OPTIONS
    }
    status_counts['All'] = base_query.count()

    query = base_query
    if selected_status != 'All':
        query = query.filter(WorkItem.progress == selected_status)
    if selected_priority:
        query = query.filter(WorkItem.priority == selected_priority)

    sort_columns = {
        'priority': WorkItem.priority,
        'deadline': WorkItem.deadline,
        'title': WorkItem.w_title,
    }
    query = query.order_by(sort_columns.get(selected_sort, WorkItem.priority).asc())
    work_items = query.all()          # no extra filter_by here

    # all assignees for the visible work items, grouped by work item id
    assignees_by_item = {}
    ids = [w.work_item_id for w in work_items]
    if ids:
        rows = db.session.execute(
            text("""
                SELECT a.w_id, u.user_id, u.full_name, u.picture
                FROM assignees a
                JOIN users u ON u.user_id = a.u_id
                WHERE a.w_id IN :ids
            """).bindparams(bindparam("ids", expanding=True)),
            {"ids": ids}
        ).mappings().all()
        for r in rows:
            assignees_by_item.setdefault(r["w_id"], []).append(r)

    return render_template(
        'user/task.html',
        work_items=work_items,
        assignees_by_item=assignees_by_item,
        user=user,
        selected_status=selected_status,
        selected_priority=selected_priority,
        selected_sort=selected_sort,
        status_counts=status_counts,
        sort_options={'priority': 'Priority', 'deadline': 'Deadline', 'title': 'Title'},
        filter_options={'high': 'High', 'medium': 'Medium', 'low': 'Low'},
        today=date.today()
    )


import traceback
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, jsonify, session, url_for
from sqlalchemy import text
from app import db
from app.models import User
from app.routes.user.user import user_required

calendar_bp = Blueprint('calendar', __name__)


def to_date(v):
    """Accept date, datetime or 'YYYY-MM-DD' string."""
    if not v:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])


def task_link(work_item_id):
    try:
        return url_for('task.task', work_item_id=work_item_id)
    except Exception:
        return '#'   # endpoint name is wrong, calendar still works


@calendar_bp.route('/calendar')
def user_calendar():
    denied = user_required()
    if denied:
        return denied

    user = User.query.filter_by(user_id=session.get('user_id')).first()
    return render_template('user/calendar.html', user=user, active_page='calendar')


@calendar_bp.route('/api/calendar_events')
def calendar_events():
    denied = user_required()
    if denied:
        return denied

    try:
        user_id = session.get('user_id')

        query = text("""
            SELECT w.work_item_id, w.w_title, w.start_date, w.end_date,
            w.deadline, w.progress, w.priority
            FROM work_items w
            WHERE w.u_id = :user_id
               OR EXISTS (
                    SELECT 1 FROM assignees a
                    WHERE a.w_id = w.work_item_id
                      AND a.u_id = :user_id
               )
        """)
        rows = db.session.execute(query, {"user_id": user_id}).fetchall()

        events = []
        for t in rows:
            deadline_d = to_date(t.deadline)
            if not deadline_d:
                continue  # no deadline, so nothing to show

            events.append({
                'id': t.work_item_id,
                'title': t.w_title,
                'start': deadline_d.isoformat(),
                'end': None,
                'url': task_link(t.work_item_id),
                'extendedProps': {
                    'status': t.progress,
                    'priority': t.priority,
                    'deadline': deadline_d.isoformat(),
                },
            })

        return jsonify(events)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': type(e).__name__, 'detail': str(e)}), 500
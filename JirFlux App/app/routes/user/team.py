from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from sqlalchemy import text
from app import db
from app.models import Team, User, Connection
from app.routes.user.user import user_required

team_bp = Blueprint('team', __name__)


@team_bp.route('/team')
def team():
    denied = user_required()
    if denied:
        return denied

    user = User.query.get(session["user_id"])

    user_team = Team.query.filter_by(u_id=session["user_id"]).first()

    if user_team is None:
        user_team = Team(u_id=session["user_id"])
        db.session.add(user_team)
        db.session.commit()

    # get team members
    query = text("""
        SELECT u.username, u.email_id, u.picture, u.bio FROM team_member tm
        JOIN team t ON tm.team_id = t.team_id
        JOIN users u ON tm.user_id = u.user_id
        WHERE t.u_id = :user_id;
    """)
    result = db.session.execute(query, {"user_id": session["user_id"]})

    count_query = text("""
        SELECT COUNT(tm.user_id) FROM team_member tm
        JOIN team t ON tm.team_id = t.team_id
        WHERE t.u_id = :user_id;
    """)
    count_result = db.session.execute(count_query, {"user_id": session["user_id"]})

    project_count = text("""
        SELECT COUNT(DISTINCT p.project_id)
        FROM users u
        JOIN projects p ON p.u_id = u.user_id
        JOIN work_items w ON p.project_id = w.p_id
        JOIN assignees a ON a.w_id = w.work_item_id
        WHERE p.u_id = :user_id OR a.u_id = :user_id;
    """)
    project_result = db.session.execute(project_count, {"user_id": session["user_id"]})

    tasks_query = text("""
        SELECT COUNT(DISTINCT w.work_item_id) FROM work_items w
        LEFT JOIN assignees a ON w.work_item_id = a.w_id
        WHERE w.u_id = :user_id OR a.u_id = :user_id;
    """)
    tasks_result = db.session.execute(tasks_query, {"user_id": session["user_id"]})

    incoming_requests = Connection.query.filter_by(
        receiver_id=session["user_id"],
        status='pending'
    ).order_by(Connection.created_at.desc()).all()

    return render_template(
        'user/team.html',
        user=user,
        team_members=result.fetchall(),
        team_count=count_result.scalar(),
        project_count=project_result.scalar(),
        tasks=tasks_result.scalar(),
        incoming_requests=incoming_requests,
        active_page='team'
    )
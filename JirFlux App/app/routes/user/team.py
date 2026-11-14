from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from sqlalchemy import text
from app import db
from app.models import Team, TeamMember, User, Connection
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
        SELECT u.user_id, u.username, u.email_id, u.picture, u.bio 
        FROM team_member tm
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
    
    rows = result.fetchall()
    print("TEAM ROW FIELDS:", rows[0]._fields if rows else "no rows")


    return render_template(
        'user/team.html',
        user=user,
        team_members=rows,
        team_count=count_result.scalar(),
        project_count=project_result.scalar(),
        tasks=tasks_result.scalar(),
        incoming_requests=incoming_requests,
        active_page='team'
    )
    
from sqlalchemy import and_, or_
from app.models import Team, TeamMember, User, Connection


@team_bp.route('/team/remove/<int:member_id>', methods=['POST'])
def remove_member(member_id):
    denied = user_required()
    if denied:
        return denied

    uid = session["user_id"]

    if member_id == uid:
        flash("You cannot remove yourself.", "error")
        return redirect(url_for('team.team'))

    # Ownership check: the person must be in MY team
    my_team = Team.query.filter_by(u_id=uid).first()
    removed = 0
    if my_team:
        removed = TeamMember.query.filter_by(
            team_id=my_team.team_id, user_id=member_id
        ).delete()

    if not removed:
        db.session.rollback()
        flash("Member not found in your team.", "error")
        return redirect(url_for('team.team'))

    # Reverse side: remove me from their team
    their_team = Team.query.filter_by(u_id=member_id).first()
    if their_team:
        TeamMember.query.filter_by(
            team_id=their_team.team_id, user_id=uid
        ).delete()

    # Remove the connection in either direction
    Connection.query.filter(
        or_(
            and_(Connection.sender_id == uid, Connection.receiver_id == member_id),
            and_(Connection.sender_id == member_id, Connection.receiver_id == uid),
        )
    ).delete(synchronize_session=False)

    db.session.commit()
    flash("Member removed from your team.", "success")
    return redirect(url_for('team.team'))
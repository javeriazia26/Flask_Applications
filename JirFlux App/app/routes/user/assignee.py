# app/routes/user/assignee.py
from sqlalchemy import or_, text

from flask import Blueprint, redirect, url_for, flash, session, request, abort
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import ProjectMember, WorkItem, Project, Assignee
from app.routes.user.notification import create_notification
from app.routes.user.project_member import project_access, is_project_person
from app.routes.user.user import log_action, user_required


assignee_bp = Blueprint('assignee', __name__)


def picture_url(picture):
    if not picture:
        return None
    return url_for('static', filename=picture.replace('static/', ''))

def get_assignees(w_id):
    """Return a list of assignees for a given work item."""
    assignee_query = text("""
        SELECT w.p_id, a.w_id, u.user_id, u.username, u.picture
        FROM assignees a
        JOIN work_items w ON w.work_item_id = a.w_id
        JOIN users u ON u.user_id = a.u_id
        WHERE w.work_item_id = :w_id
        ORDER BY u.username
    """)
    result = db.session.execute(assignee_query, {"w_id": w_id})
    return result.fetchall()

# Assign a person to an existing work item
@assignee_bp.route('/project/<int:p_id>/workitem/<int:w_id>/assign', methods=['POST'])
def assign_workitem(p_id, w_id):
    denied = user_required()
    if denied:
        return denied

    proj = Project.query.get_or_404(p_id)
    work_item = WorkItem.query.get_or_404(w_id)
    if work_item.p_id != p_id:                      # item must belong to this project
        abort(404)

    if not project_access(proj):
        flash("You don't have permission to assign people.", "error")
        return redirect(url_for('project.project'))

    try:
        target_id = int(request.form.get('user_id', ''))
    except ValueError:
        flash("Choose a person to assign.", "error")
        return redirect(url_for('project.project'))

    if not is_project_person(proj, target_id):
        flash("Only the owner or members of this project can be assigned.", "error")
        return redirect(url_for('project.project'))

    issignee = Assignee.query.filter_by(w_id=w_id, u_id=target_id).first()
    isowner = work_item.u_id == target_id
    if issignee or isowner:
        flash("That person is already assigned.", "info")
        return redirect(url_for('project.project'))

    try:
        db.session.add(Assignee(w_id=w_id, u_id=target_id))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Could not assign that person.", "error")
        return redirect(url_for('project.project'))

    flash("Person assigned.", "success")
    if target_id != session['user_id']:
        create_notification(
            user_id=target_id,
            title="Work Item Assigned",
            message=f'{session["username"]} assigned you to "{work_item.w_title}".',
            notification_type="workitem"
        )
        
    return redirect(url_for('project.project'))


# Remove a person from a work item
@assignee_bp.route('/project/<int:p_id>/workitem/<int:w_id>/unassign/<int:user_id>', methods=['POST'])
def unassign_workitem(p_id, w_id, user_id):
    denied = user_required()
    if denied:
        return denied

    proj = Project.query.get_or_404(p_id)
    work_item = WorkItem.query.get_or_404(w_id)
    if work_item.p_id != p_id:
        abort(404)

    if not project_access(proj):
        flash("You don't have permission to change assignees.", "error")
        return redirect(url_for('project.project'))

    assignment = Assignee.query.filter_by(w_id=w_id, u_id=user_id).first_or_404()
    db.session.delete(assignment)
    db.session.commit()

    flash("Person unassigned.", "success")
    return redirect(url_for('project.project'))

def _attach_assignees(projects):
    """Give every work item its 'assignees' list and its 'creator'."""
    for p in projects.values():
        for wi in p['work_items'].values():
            wi['assignees'] = []
            wi['creator'] = None
    if not projects:
        return projects

    ids = list(projects.keys())

    # 1) Assignees only
    rows = db.session.execute(text("""
        SELECT w.p_id, a.w_id, u.user_id, u.username, u.picture
        FROM assignees a
        JOIN work_items w ON w.work_item_id = a.w_id
        JOIN users u ON u.user_id = a.u_id
        WHERE w.p_id = ANY(:ids)
        ORDER BY u.username
    """), {"ids": ids}).fetchall()

    for r in rows:
        wi = projects[r.p_id]['work_items'].get(r.w_id)
        if wi is not None:
            wi['assignees'].append({
                'id': r.user_id, 'username': r.username,
                'picture': picture_url(r.picture)})

    # 2) Creators: one per work item, with or without assignees
    rows = db.session.execute(text("""
        SELECT w.p_id, w.work_item_id AS w_id,
               u.user_id, u.username, u.picture
        FROM work_items w
        JOIN users u ON u.user_id = w.u_id
        WHERE w.p_id = ANY(:ids)
    """), {"ids": ids}).fetchall()

    for r in rows:
        wi = projects[r.p_id]['work_items'].get(r.w_id)
        if wi is not None:
            wi['creator'] = {
                'id': r.user_id, 'username': r.username,
                'picture': picture_url(r.picture)}

    return projects
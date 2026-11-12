from operator import and_
from app import db
from app.routes.user.validators import clean_github_url
from flask import Blueprint, abort, current_app, render_template, redirect, url_for, flash, session, request
from flask_login import current_user
from sqlalchemy import or_, text
from app import db
from datetime import date, datetime
from app.routes.user.notification import create_notification
from app.routes.user.user import user_required
from app.models import ProjectMember, User, Project, Connection, Assignee, WorkItem
from app.routes.user.comment import attach_comments
from app.routes.user.assignee import _attach_assignees
from flask_wtf import FlaskForm

project_bp = Blueprint('project', __name__)

today = date.today()

def _fetch_project_rows(user_id):
    """Run the raw SQL and return every (work item x assignee) row the
    user is allowed to see, across all of their projects."""
    query = text("""
        SELECT
            w.work_item_id,
            w.w_title       AS w_title,
            w.priority      AS priority,
            w.progress      AS work_status,
            w.w_des         AS work_description,
            w.start_date    AS work_start_date,
            w.end_date      AS work_end_date,
            p.project_id,
            p.p_title,
            p.p_des      AS description,
            p.start_date,
            p.github_url,
            p.deadline,
            p.current_status,
            p.u_id           AS project_owner_id,
            a.assignee_id,
            a.u_id            AS assignee_user_id,
            au.username       AS assignee_username,
            pm.role           AS my_role
        FROM projects p
        LEFT JOIN project_member pm
        ON pm.p_id = p.project_id AND pm.user_id = :user_id
        LEFT JOIN work_items w
            ON w.p_id = p.project_id
        LEFT JOIN assignees a
            ON w.work_item_id = a.w_id
        LEFT JOIN users au
            ON a.u_id = au.user_id
        WHERE p.u_id = :user_id OR pm.user_id = :user_id
        ORDER BY p.project_id, w.work_item_id
    """)
    return db.session.execute(query, {"user_id": user_id}).fetchall()


def _group_rows_into_projects(rows):
    """Collapse the flat (work item x assignee) rows into one dict per
    project, with nested work_items / assignees lists - so callers and
    templates don't have to do this bookkeeping themselves."""
    projects = {}
    for r in rows:
        pid = r.project_id
        if pid not in projects:
            projects[pid] = {
                'p_id': pid,
                'title': r.p_title,
                'description': r.description,
                'owner_id': r.project_owner_id,
                'start_date': r.start_date,
                'deadline': r.deadline,
                'github_url': r.github_url,
                'current_status': r.current_status,
                'work_items': {},   # keyed by work_item_id to dedupe across assignee rows
                'assignees': {},    # keyed by user id to dedupe
                'my_role': r.my_role,
            } 

        proj = projects[pid]

        if r.work_item_id is not None and r.work_item_id not in proj['work_items']:
            proj['work_items'][r.work_item_id] = {
                'id': r.work_item_id,
                'w_title': r.w_title,
                'priority': r.priority,
                'status': r.work_status,
                'description': r.work_description,
                'start_date': r.work_start_date,
                'deadline': r.deadline,
                'end_date': r.work_end_date,
            }


        if r.assignee_user_id is not None and r.assignee_user_id not in proj['assignees']:
            proj['assignees'][r.assignee_user_id] = {
                'id': r.assignee_user_id,
                'username': r.assignee_username,
            }

    return projects


def _finalize_project_stats(projects, user_id):
    """Turn the nested dicts into lists and compute progress / permissions
    for each project, in place."""
    for proj in projects.values():
        proj['work_items'] = list(proj['work_items'].values())
        proj['assignees'] = list(proj['assignees'].values())
        proj['total'] = len(proj['work_items'])
        proj['done'] = sum(
            1 for wi in proj['work_items']
            if (wi['status'] or '').strip().lower() == 'completed'
        )
        # Owner can always add work items; a non-owner member can too,
        # unless their role is 'visitor'.
        proj['can_add_workitem'] = (
            proj['owner_id'] == user_id
            or (proj['my_role'] is not None and proj['my_role'] != 'visitor')
        )

        
    return projects

# Paste this function into project.py, next to _attach_comments.
def _attach_files(projects):
    """Give every work item its own 'files' list (oldest first)."""
    for p in projects.values():
        for wi in p['work_items'].values():
            wi['files'] = []
    if not projects:
        return projects

    rows = db.session.execute(text("""
        SELECT w.p_id, f.w_id, f.file_id, f.f_title, f.f_type, f.f_size, f.f_upload_time,
               u.user_id, u.username, u.picture
        FROM files f
        JOIN work_items w ON w.work_item_id = f.w_id
        JOIN users u ON u.user_id = f.u_id
        WHERE w.p_id = ANY(:ids)
        ORDER BY f.f_upload_time ASC
    """), {"ids": list(projects.keys())}).fetchall()

    for r in rows:
        wi = projects[r.p_id]['work_items'].get(r.w_id)
        if wi is not None:
            wi['files'].append({
                'id': r.file_id,
                'name': r.f_title,
                'type': r.f_type,
                'size': r.f_size,
                'time': r.f_upload_time.isoformat() + 'Z',
                'user_id': r.user_id,
                'username': r.username,
                'picture': _picture_url(r.picture),
            })
    return projects


from app.routes.user.validators import clean_github_url

# Set or clear the project's GitHub repo link (owner only)
@project_bp.route('/<int:p_id>/github', methods=['POST'])
def set_github(p_id):
    denied = user_required()
    if denied:
        return denied

    project = Project.query.get_or_404(p_id)
    if project.u_id != session['user_id']:
        abort(403)

    clean_url, error = clean_github_url(request.form.get('github_url'))
    if error:
        flash(error, "error")
        return redirect(url_for('project.project'))

    project.github_url = clean_url   # None means "remove the link"
    try:
        db.session.commit()
        flash("Repository link saved." if clean_url else "Repository link removed.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("github save failed")
        flash(f"Could not save the link: {e}", "error")
    return redirect(url_for('project.project'))

# Add Project Member (owner only, must be an accepted friend)
@project_bp.route('/project/<int:p_id>/member/add', methods=['POST'])
def add_member(p_id):
    denied = user_required()
    if denied:
        return denied

    owner_id = session['user_id']
    proj = Project.query.get_or_404(p_id)

    if proj.u_id != owner_id:
        flash("Only the project owner can add members.", "error")
        return redirect(url_for('project.project'))

    username = (request.form.get('username') or '').strip()
    role = request.form.get('role') or 'member'
    if role not in ('member', 'visitor'):
        role = 'member'

    if not username:
        flash("Enter a username.", "error")

        return redirect(url_for('project.project'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'No user named "{username}" was found.', "error")
        return redirect(url_for('project.project'))

    if user.user_id == owner_id:
        flash("You are the owner of this project already.", "error")
        return redirect(url_for('project.project'))

    is_friend = Connection.query.filter(
        Connection.status == 'accepted',
        or_(
            and_(Connection.sender_id == owner_id, Connection.receiver_id == user.user_id),
            and_(Connection.sender_id == user.user_id, Connection.receiver_id == owner_id),
        )
    ).first()
    if not is_friend:
        flash(f'"{username}" is not in your friend list. Connect with them first.', "error")
        return redirect(url_for('project.project'))

    if ProjectMember.query.filter_by(p_id=p_id, user_id=user.user_id).first():
        flash(f'"{username}" is already a member of this project.', "error")
        return redirect(url_for('project.project'))

    db.session.add(ProjectMember(
        p_id=p_id,
        user_id=user.user_id,
        role=role,
        status='accepted',
        invited_by=owner_id,
    ))
    db.session.commit()

    flash(f'"{username}" was added to the project.', "success")
    create_notification(
        user_id=user.user_id,
        title="Added to Project",
        message=f'You were added to project "{proj.p_title}" by {session["username"]}.',
        notification_type="project"
    )
    return redirect(url_for('project.project'))


# Remove Project Member (owner only)
@project_bp.route('/project/<int:p_id>/member/remove/<int:user_id>', methods=['POST'])
def remove_member(p_id, user_id):
    denied = user_required()
    if denied:
        return denied

    proj = Project.query.get_or_404(p_id)

    if proj.u_id != session['user_id']:
        flash("Only the project owner can remove members.", "error")
        return redirect(url_for('project.project'))

    member = ProjectMember.query.filter_by(p_id=p_id, user_id=user_id).first_or_404()
    wi_ids = [w.work_item_id for w in WorkItem.query.filter_by(p_id=p_id).all()]
    if wi_ids:
        Assignee.query.filter(
            Assignee.w_id.in_(wi_ids),
            Assignee.u_id == user_id
        ).delete(synchronize_session=False)
    
    db.session.delete(member)
    db.session.commit()

    flash("Member removed.", "success")
    return redirect(url_for('project.project'))

def _picture_url(picture):
    if not picture:
        return None
    return url_for('static', filename=picture.replace('static/', ''))


def _attach_members(projects):
    """Add the owner and the accepted members to each project dict."""
    for p in projects.values():
        p['members'] = []
        p['owner'] = None
    if not projects:
        return projects
    ids = list(projects.keys())

    for r in db.session.execute(text("""
        SELECT p.project_id, u.user_id, u.username, u.picture
        FROM projects p JOIN users u ON u.user_id = p.u_id
        WHERE p.project_id = ANY(:ids)
    """), {"ids": ids}).fetchall():
        projects[r.project_id]['owner'] = {
            'id': r.user_id, 'username': r.username, 'picture': _picture_url(r.picture)}

    for r in db.session.execute(text("""
        SELECT pm.p_id, pm.user_id, pm.role, u.username, u.picture
        FROM project_member pm JOIN users u ON u.user_id = pm.user_id
        WHERE pm.p_id = ANY(:ids) AND pm.status = 'accepted'
        ORDER BY u.username
    """), {"ids": ids}).fetchall():
        projects[r.p_id]['members'].append({
            'id': r.user_id, 'username': r.username, 'role': r.role,
            'picture': _picture_url(r.picture)})
    return projects

def get_user_projects(user_id):
    """Everything the project list page needs: one dict per project the
    user owns or is assigned to, each with its work items, assignees,
    progress and permissions already computed."""
    rows = _fetch_project_rows(user_id)
    projects = _group_rows_into_projects(rows)
    projects = _attach_members(projects)  
    projects = _attach_assignees(projects)
    projects = attach_comments(projects)
    projects = _attach_files(projects) 
    
    return _finalize_project_stats(projects, user_id)


@project_bp.route('/project')
def project():

    # Check whether user is logged in
    denied = user_required()
    if denied:
        return denied

    # Get logged-in user
    user = User.query.filter_by(user_id=session["user_id"]).first()

    projects = get_user_projects(session["user_id"])

    return render_template(
        'user/project.html',
        user=user,
        current_user_id=session["user_id"],
        form=FlaskForm(),
        projects=projects,
        active_page='project'
    )


# Add Project
@project_bp.route('/project/add', methods=['POST'])
def add_project():
    denied = user_required()
    if denied:
        return denied

    # Project details from form
    p_title = request.form.get('p_title')
    p_des = request.form.get('p_des')
    start_date_str = request.form.get('start_date')
    deadline_str = request.form.get('deadline')
    current_status = request.form.get('current_status')
    # owner of project
    u_id = session['user_id']

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

    new_project = Project(
        p_title=p_title,
        p_des=p_des,
        start_date=start_date,
        deadline=deadline,
        current_status=current_status,
        u_id=u_id
    )

    db.session.add(new_project)
    db.session.commit()
    flash(f'The "{new_project.p_title}" project has been added successfully.', "success")
    notification_message = f'Project {new_project.p_title} has been created by {session["username"]}.'
    create_notification(
        user_id=u_id,
        title="Project Created",
        message=notification_message,
        notification_type="project"
    )
    return redirect(url_for('project.project'))


# Edit Project
@project_bp.route('/project/edit/<int:p_id>', methods=['POST'])
def edit_project(p_id):
    denied = user_required()
    if denied:
        return denied

    proj = Project.query.get_or_404(p_id)
    u_id = session['user_id']

    if u_id != proj.u_id:  # only the owner can edit
        flash("You don't have permission to edit this project.", "error")
        return redirect(url_for('project.project'))

    proj.p_title = request.form.get('p_title')
    proj.p_des = request.form.get('p_des')
    start_date = request.form.get('start_date')
    deadline = request.form.get('deadline')
    proj.current_status = request.form.get('current_status')

    proj.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
    proj.deadline = datetime.strptime(deadline, '%Y-%m-%d').date() if deadline else None

    db.session.commit()
    flash(f'The {proj.p_title} project has been updated successfully.', "success")

    create_notification(
        user_id=u_id,
        title="Project Updated",
        message=f'Project {proj.p_title} has been updated by {session["username"]}.',
        notification_type="project"
    )

    return redirect(url_for('project.project'))


# Delete Project
@project_bp.route('/project/delete/<int:p_id>', methods=['POST'])
def delete_project(p_id):
    denied = user_required()
    if denied:
        return denied

    project = Project.query.get_or_404(p_id)
    p_title = project.p_title

    if session['user_id'] != project.u_id:  # only the owner can delete
        flash("You don't have permission to delete this project.", "error")
        return redirect(url_for('project.project'))

    db.session.delete(project)
    db.session.commit()
    flash(f'The "{p_title}" project has been deleted successfully.', "success")
    create_notification(
        user_id=session['user_id'],
        title="Project Deleted",
        message=f'Project {p_title} has been deleted by {session["username"]}.',
        notification_type="project"
    )

    return redirect(url_for('project.project'))

@project_bp.route('/project/<int:p_id>/leave', methods=['POST'])
def leave_project(p_id):
    denied = user_required()
    if denied:
        return denied

    me = session['user_id']
    project = Project.query.get_or_404(p_id)

    # The owner can't leave their own project; they delete it instead
    if project.u_id == me:
        flash("Owners can't leave their own project. Delete it instead.", "error")
        return redirect(url_for('project.project'))

    # Only the logged-in user's own membership in THIS project
    member = ProjectMember.query.filter_by(p_id=p_id, user_id=me).first()
    if not member:
        flash("You're not a member of this project.", "error")
        return redirect(url_for('project.project'))

    # Remove their assignments on this project's work items
    item_ids = [w.work_item_id for w in WorkItem.query.filter_by(p_id=p_id).all()]
    if item_ids:
        Assignee.query.filter(
            Assignee.u_id == me, Assignee.w_id.in_(item_ids)
        ).delete(synchronize_session=False)

    WorkItem.query.filter_by(p_id=p_id, u_id=me).update({'u_id': Project.u_id})  # Reassign their work items to the project owner
    
    db.session.delete(member)
    db.session.commit()

    create_notification(
        user_id=project.u_id,
        title="Member Left Project",
        message=f'{session["username"]} left "{project.p_title}".',
        notification_type="project"
    )

    flash("You have left the project.", "success")
    return redirect(url_for('project.project'))
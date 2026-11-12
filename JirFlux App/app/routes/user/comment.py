from sqlalchemy import text

from flask import Blueprint, redirect, url_for, flash, session, request, abort
from app import db
from app.models import Comment, WorkItem, Project
from app.routes.user.user import user_required
from app.routes.user.project_member import is_project_person

comment_bp = Blueprint('comment', __name__)

MAX_COMMENT_LENGTH = 1000


def _clean_comment_text():
    """Read, trim and check the comment text from the form.
    Returns (text, error_message). One of the two is always None."""
    body = (request.form.get('comment') or '').strip()
    if not body:
        return None, "Write something before posting."
    if len(body) > MAX_COMMENT_LENGTH:
        return None, f"Comments can be at most {MAX_COMMENT_LENGTH} characters."
    return body, None


def _load_comment(project_id, work_item_id, comment_id):
    """Load the project, work item and comment, and make sure they belong together."""
    proj = Project.query.get_or_404(project_id)
    work_item = WorkItem.query.get_or_404(work_item_id)
    if work_item.p_id != project_id:
        abort(404)
    comment = Comment.query.get_or_404(comment_id)
    if comment.w_id != work_item_id:
        abort(404)
    return proj, comment


# Add a comment (anyone in the project, including visitors)
@comment_bp.route('/project/<int:project_id>/workitem/<int:work_item_id>/comment/add', methods=['POST'])
def add_comment(project_id, work_item_id):
    denied = user_required()
    if denied:
        return denied

    proj = Project.query.get_or_404(project_id)
    work_item = WorkItem.query.get_or_404(work_item_id)
    if work_item.p_id != project_id:                      # item must belong to this project
        abort(404)

    if not is_project_person(proj, session['user_id']):
        flash("Only people in this project can comment.", "error")
        return redirect(url_for('project.project'))

    body, error = _clean_comment_text()
    if error:
        flash(error, "error")
        return redirect(url_for('project.project'))

    db.session.add(Comment(comment=body, w_id=work_item_id, u_id=session['user_id']))
    db.session.commit()

    flash("Comment posted.", "success")
    return redirect(url_for('project.project'))


# Edit a comment (its author only)
@comment_bp.route('/project/<int:project_id>/workitem/<int:work_item_id>/comment/edit/<int:comment_id>', methods=['POST'])
def edit_comment(project_id, work_item_id, comment_id):
    denied = user_required()
    if denied:
        return denied

    proj, comment = _load_comment(project_id, work_item_id, comment_id)

    if comment.u_id != session['user_id']:
        flash("You can only edit your own comments.", "error")
        return redirect(url_for('project.project'))

    body, error = _clean_comment_text()
    if error:
        flash(error, "error")
        return redirect(url_for('project.project'))

    comment.comment = body
    db.session.commit()

    flash("Comment updated.", "success")
    return redirect(url_for('project.project'))


# Delete a comment (its author only)
@comment_bp.route('/project/<int:project_id>/workitem/<int:work_item_id>/comment/delete/<int:comment_id>', methods=['POST'])
def delete_comment(project_id, work_item_id, comment_id):
    denied = user_required()
    if denied:
        return denied

    proj, comment = _load_comment(project_id, work_item_id, comment_id)

    if comment.u_id != session['user_id']:
        flash("You can only delete your own comments.", "error")
        return redirect(url_for('project.project'))

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted.", "success")
    return redirect(url_for('project.project'))

def _picture_url(picture):
    if not picture:
        return None
    return url_for('static', filename=picture.replace('static/', ''))


def attach_comments(projects):
    """Give every work item its own 'comments' list."""
    for p in projects.values():
        for wi in p['work_items'].values():
            wi['comments'] = []
    if not projects:
        return projects

    rows = db.session.execute(text("""
        SELECT w.p_id, c.w_id, c.comment_id, c.u_id, c.comment,
               c.c_upload_time, u.username, u.picture
        FROM comments c
        JOIN work_items w ON w.work_item_id = c.w_id
        JOIN users u ON u.user_id = c.u_id
        WHERE w.p_id = ANY(:ids)
        ORDER BY c.c_upload_time
    """), {"ids": list(projects.keys())}).fetchall()

    for r in rows:
        wi = projects[r.p_id]['work_items'].get(r.w_id)
        if wi is not None:
            wi['comments'].append({
                'id': r.comment_id,
                'user_id': r.u_id,
                'username': r.username,
                'picture': _picture_url(r.picture),
                'text': r.comment,
                'time': r.c_upload_time.strftime('%Y-%m-%dT%H:%M:%S')})
    return projects
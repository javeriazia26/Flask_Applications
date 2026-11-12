from datetime import datetime

from flask import Blueprint, redirect, session, url_for, flash
from app import db
from app.models import Assignee, Project, ProjectMember, WorkItem
from app.routes.user.notification import create_notification

from app.routes.user.user import log_action, user_required
from app.routes.admin.admin import audit_log_action


project_member_bp = Blueprint('project_member',__name__)


def project_access(proj):
    """True if the logged-in user can edit things in this project (owner, or member who isn't a visitor)."""
    uid = session['user_id']
    if proj.u_id == uid:
        return True
    m = ProjectMember.query.filter_by(
        p_id=proj.project_id, user_id=uid, status='accepted').first()
    return bool(m and m.role != 'visitor')
 
 
def is_project_person(proj, user_id):
    """True if this user is the owner or an accepted member of the project."""
    if proj.u_id == user_id:
        return True
    return ProjectMember.query.filter_by(
        p_id=proj.project_id, user_id=user_id, status='accepted').first() is not None
 


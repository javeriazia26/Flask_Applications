from flask import Blueprint, render_template, session
from app.models import AuditLog, User
from app.routes.admin.admin import admin_required

audit_log_bp = Blueprint('audit_log', __name__)

@audit_log_bp.route('/admin/audit_log')
def audit_log():
    denied = admin_required()
    if denied:
        return denied

    user = User.query.get(session['user_id'])
    logs = AuditLog.query.order_by(AuditLog.date.desc(), AuditLog.time.desc()).all()
    return render_template('admin/audit_log.html', audit_logs=logs, user=user, active_page='audit_log')

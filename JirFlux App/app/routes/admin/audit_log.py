from flask import Blueprint, render_template
from app.models import AuditLog
from app.routes.admin.admin import admin_required

audit_log_bp = Blueprint('audit_log', __name__)

@audit_log_bp.route('/admin/audit_log')
def audit_log():
    denied = admin_required()
    if denied:
        return denied

    logs = AuditLog.query.order_by(AuditLog.date.desc(), AuditLog.time.desc()).all()
    return render_template('admin/audit_log.html', audit_logs=logs)

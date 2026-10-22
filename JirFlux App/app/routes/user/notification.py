from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import current_user

from app import db
from app.models import Notification
from app.routes.user.user import user_required


notification_bp = Blueprint('notification', __name__)


# =========================
# Helpers
# =========================

def _get_owned_notification_or_404(notification_id, user_id):
    """Fetch a notification, scoped to the logged-in user, or 404."""
    return Notification.query.filter_by(
        notification_id=notification_id,
        u_id=user_id
    ).first_or_404()


def create_notification(user_id, title, message, notification_type, n_time=None):
    """Create and persist a notification. Timestamps are always stored in UTC."""
    notification = Notification(
        u_id=user_id,
        n_title=title,
        n_des=message,
        n_time=n_time or datetime.now(timezone.utc),
        notification_type=notification_type
    )
    db.session.add(notification)
    db.session.commit()
    return notification


# =========================
# View User Notifications
# =========================
@notification_bp.route('/notifications')
def notifications():
    denied = user_required()
    if denied:
        return denied

    user_id = session.get("user_id")

    notifications = (
        Notification.query
        .filter_by(u_id=user_id)
        .order_by(Notification.n_time.desc())
        .all()
    )

    # Times are stored in UTC; the template converts to the viewer's
    # local timezone client-side, so no "now" or timezone math is needed here.
    return render_template(
        'user/notification.html',
        user=current_user,
        notifications=notifications
    )


# =========================
# Mark Notification as Read
# =========================
@notification_bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_read(notification_id):
    denied = user_required()
    if denied:
        return denied

    user_id = session.get("user_id")
    notification = _get_owned_notification_or_404(notification_id, user_id)

    notification.is_read = True
    db.session.commit()

    return redirect(url_for('notification.notifications'))


# =========================
# Delete Notification
# =========================
@notification_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
def delete_notification(notification_id):
    denied = user_required()
    if denied:
        return denied

    user_id = session.get("user_id")
    notification = _get_owned_notification_or_404(notification_id, user_id)

    db.session.delete(notification)
    db.session.commit()

    flash("Notification deleted successfully.", "success")
    return redirect(url_for('notification.notifications'))


# =========================
# Mark All Notifications as Read
# =========================
@notification_bp.route('/notifications/mark_all_read', methods=['POST'])
def mark_all_read():
    denied = user_required()
    if denied:
        return denied

    user_id = session.get("user_id")

    Notification.query.filter_by(
        u_id=user_id,
        is_read=False
    ).update({"is_read": True})
    db.session.commit()

    flash("All notifications marked as read.", "success")
    return redirect(url_for('notification.notifications'))
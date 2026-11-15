# app/routes/admin/admin_profile.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import db
from app.models import User
from app.routes.admin.admin import admin_required, audit_log_action
from app.routes.user.profile import update_profile

admin_profile_bp = Blueprint("admin_profile", __name__)


@admin_profile_bp.route("/admin/profile")
def admin_profile():
    denied = admin_required()
    if denied:
        return denied

    user = db.session.get(User, session["user_id"])

    return render_template(
        "admin/admin_profile.html",
        user=user,
        base_template="user/admin_base.html",
        edit_url=url_for("admin_profile.admin_edit_profile"),
    )


@admin_profile_bp.route("/admin/profile/edit", methods=["POST"])
def admin_edit_profile():
    denied = admin_required()
    if denied:
        return denied

    user = db.session.get(User, session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_profile.admin_profile"))

    ok, message = update_profile(user, request.form, request.files)

    if ok:
        audit_log_action(
            "profile-updated",
            "credential",
            user_id=user.user_id,
            username=user.username,
        )

    flash(message, "success" if ok else "error")
    return redirect(url_for("admin_profile.admin_profile"))
# app/routes/user/profile.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import db
from app.models import Skill, User
from app.routes.admin.admin import audit_log_action
from app.routes.user.avatar import save_avatar
from app.routes.user.user import user_required

profile_bp = Blueprint("profile", __name__)


def update_profile(user, form, files):
    """Apply a submitted profile form to ``user`` and commit.

    Shared by the user and admin profile routes.
    Returns ``(ok, message)``. On failure nothing is saved.
    """
    new_username = form.get("username", "").strip()

    if new_username and new_username != user.username:
        taken = User.query.filter(
            User.username == new_username,
            User.user_id != user.user_id,
        ).first()
        if taken:
            return False, "Username already exists. Please choose a different username."
        user.username = new_username

    user.full_name = form.get("full_name", user.full_name)
    user.location = form.get("location", user.location)
    user.bio = form.get("bio", user.bio)

    _replace_skills(user, form.getlist("skills"))

    picture = files.get("profile_picture")
    if picture and picture.filename:
        error = save_avatar(user, picture)
        if error:
            db.session.rollback()
            return False, error

    db.session.commit()
    return True, "Profile updated successfully."


def _replace_skills(user, skill_names):
    """Replace the user's skills with a de-duplicated list."""
    for skill in list(user.skills):
        db.session.delete(skill)

    seen = set()
    for name in skill_names:
        name = name.strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            db.session.add(Skill(skill_name=name, u_id=user.user_id))


@profile_bp.route("/profile")
def profile():
    denied = user_required()
    if denied:
        return denied

    user = db.session.get(User, session["user_id"])

    return render_template(
        "user/profile.html",
        user=user,
        base_template="user/base.html",
        edit_url=url_for("profile.edit_profile"),
    )


@profile_bp.route("/profile/edit", methods=["POST"])
def edit_profile():
    denied = user_required()
    if denied:
        return denied

    user = db.session.get(User, session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("profile.profile"))

    ok, message = update_profile(user, request.form, request.files)

    if ok:
        audit_log_action(
            "profile-updated",
            "credential",
            user_id=user.user_id,
            username=user.username,
        )

    flash(message, "success" if ok else "error")
    return redirect(url_for("profile.profile"))
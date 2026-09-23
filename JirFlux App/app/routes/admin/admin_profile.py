from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app import db
from app.models import Skill, User
from app.routes.admin.admin import admin_required, audit_log_action
from werkzeug.utils import secure_filename

admin_profile_bp = Blueprint('admin_profile', __name__)


# Display admin profile
@admin_profile_bp.route('/admin/profile')
def admin_profile():
    denied = admin_required()
    if denied:
        return denied

    user = User.query.get(session["user_id"])

    return render_template(
        'admin/admin_profile.html',
        user=user,
        base_template='user/admin_base.html',   
        edit_url=url_for('admin_profile.admin_edit_profile')
    )


# Update admin profile
@admin_profile_bp.route('/admin/profile/edit', methods=['POST'])
def admin_edit_profile():
    denied = admin_required()
    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for('admin_profile.admin_profile'))

    # -------------------------
    # Username
    # -------------------------
    new_username = request.form.get('username')

    if new_username and new_username != user.username:

        existing_user = User.query.filter(
            User.username == new_username,
            User.user_id != user.user_id
        ).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('admin_profile.admin_profile'))

        user.username = new_username

    # -------------------------
    # Full Name, Location, Bio
    # -------------------------
    user.full_name = request.form.get('full_name', user.full_name)
    user.location = request.form.get('location', user.location)
    user.bio = request.form.get('bio', user.bio)

    # -------------------------
    # Skills (saved in the skills table)
    # -------------------------
    if 'skills_submitted' in request.form:
        skills = request.form.getlist('skills')

        # delete the old skills
        for skill in list(user.skills):
            db.session.delete(skill)

        # add the new skills
        for skill_name in skills:
            skill_name = skill_name.strip()
            if skill_name:
                db.session.add(Skill(skill_name=skill_name, u_id=session["user_id"]))

    # -------------------------
    # Profile Picture
    # -------------------------
    if 'profile_picture' in request.files:

        picture = request.files['profile_picture']

        if picture and picture.filename:
            # user id in front so two users can't overwrite each other's file
            filename = str(user.user_id) + "_" + secure_filename(picture.filename)

            picture_path = 'app/static/pictures/' + filename

            picture.save(picture_path)

            user.picture = picture_path
            

    # -------------------------
    # Save everything
    # -------------------------
    db.session.commit()

    audit_log_action(
        "profile-updated",
        "credential",
        user_id=user.user_id,
        username=user.username
    )

    flash('Profile updated successfully.', 'success')

    return redirect(url_for('admin_profile.admin_profile'))
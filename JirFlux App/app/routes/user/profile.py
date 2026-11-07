import os
from flask import Blueprint, current_app, render_template, redirect, url_for, flash, session, request
from app import db
from app.models import Skill, User
from app.routes.user.user import user_required
from app.routes.admin.admin import audit_log_action   # change if your user routes use another logger
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)


# Display user profile
@profile_bp.route('/profile')
def profile():
    denied = user_required()
    if denied:
        return denied

    user = User.query.get(session["user_id"])

    return render_template(
        'user/profile.html',
        user=user,
        base_template='user/base.html',   
        edit_url=url_for('profile.edit_profile')
    )


# Update user profile
@profile_bp.route('/profile/edit', methods=['POST'])
def edit_profile():
    denied = user_required()
    if denied:
        return denied

    user = User.query.get(session["user_id"])

    if not user:
        flash("User not found.", "error")
        return redirect(url_for('profile.profile'))

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
            return redirect(url_for('profile.profile'))

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
    skills = request.form.getlist('skills')   # returns [] if none sent

    # delete the old skills
    for skill in list(user.skills):
        db.session.delete(skill)

    # add the new skills (deduplicated)
    seen = set()
    for skill_name in skills:
        skill_name = skill_name.strip()
        if skill_name and skill_name.lower() not in seen:
            seen.add(skill_name.lower())
            db.session.add(Skill(skill_name=skill_name, u_id=user.user_id))


    # -------------------------
    # Profile Picture
    # -------------------------
    if 'profile_picture' in request.files:

            picture = request.files.get('profile_picture')

    if picture and picture.filename:
        filename = str(user.user_id) + "_" + secure_filename(picture.filename)

        pictures_dir = os.path.join(current_app.static_folder, 'pictures')
        os.makedirs(pictures_dir, exist_ok=True)

        picture.save(os.path.join(pictures_dir, filename))

        user.picture = 'pictures/' + filename

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

    return redirect(url_for('profile.profile'))
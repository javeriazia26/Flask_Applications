from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from flask_login import current_user
from app.routes.user.notification import create_notification
from app.routes.user.user import log_action, user_required
from app import db
from app.models import Team, TeamMember, User, Connection


connection_bp = Blueprint('connection', __name__)

@connection_bp.route('/connect/send/<int:user_id>', methods=['POST'])
def send_connection_request(user_id):
    denied = user_required()
    if denied:
        return denied

    # Don't allow a user to connect with themselves
    if session['user_id'] == user_id:
        flash('You cannot send a connection request to yourself.', 'error')
        return redirect(url_for('user.team', user_id=user_id))

    # Check if the user exists
    user = User.query.get(user_id)

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('user.team', user_id=session['user_id']))

    # Check whether a connection already exists
    connection = Connection.query.filter(
        ((Connection.sender_id == session['user_id']) &
            (Connection.receiver_id == user_id))
        |
        ((Connection.sender_id == user_id) &
            (Connection.receiver_id == session['user_id']))).first()

    if connection:

        if connection.status == 'pending':
            flash('Connection request already exists.', 'info')

        elif connection.status == 'accepted':
            flash('You are already connected with this user.', 'info')

        elif connection.status == 'rejected':
            # Allow sending a new request after rejection
            connection.sender_id = session['user_id']
            connection.receiver_id = user_id
            connection.status = 'pending'
            db.session.commit()

            flash('Connection request sent.', 'success')
            create_notification(
                user_id=user_id,  # notify the receiver, not the sender
                title="Connection Request",
                message=f"{session['user_id']} has sent you a connection request.",
                notification_type="connection"
            )

        elif connection.status == 'removed':
            # Allow reconnecting after unfriending
            connection.sender_id = session['user_id']
            connection.receiver_id = user_id
            connection.status = 'pending'
            db.session.commit()

            flash('Connection request sent.', 'success')

        return redirect(url_for('team.team', user_id=session['user_id']))

    # No previous connection exists
    new_connection = Connection(
        sender_id=session['user_id'],
        receiver_id=user_id,
        status='pending'
    )

    db.session.add(new_connection)
    db.session.commit()

    flash('Connection request sent.', 'success')
    create_notification(
        user_id=user_id,  # notify the receiver, not the sender
        title="Connection Request",
        message=f"{session['user_id']} has sent you a connection request.",
        notification_type="connection"
    )

    return redirect(url_for('team.team', user_id=session['user_id']))


@connection_bp.route('/connect-by-username', methods=['POST'])
def send_connection_request_by_username():
    denied = user_required()
    if denied:
        return denied

    username = (request.form.get('username') or '').strip()

    if not username:
        flash('Please enter a username.', 'error')
        return redirect(url_for('team.team', user_id=session['user_id']))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash(f'No user found with username "{username}".', 'error')
        return redirect(url_for('team.team', user_id=session['user_id']))

    # Reuse the existing route's logic exactly as-is, just resolved
    # from a username instead of a URL user_id.
    return send_connection_request(user.user_id)




@connection_bp.route('/connect/accept/<int:user_id>', methods=['POST'])
def accept_connection_request(user_id):
    denied = user_required()
    if denied:
        return denied

    if session['user_id'] == user_id:
        flash('You cannot accept a connection request from yourself.', 'error')
        return redirect(url_for('user.team', user_id=user_id))

    connection = Connection.query.filter_by(
        sender_id=user_id,
        receiver_id=session['user_id']
    ).first_or_404()

    connection.status = 'accepted'

    # sender's team — add the accepter (session user) into it
    team = Team.query.filter_by(u_id=user_id).first()
    if not team:
        team = Team(u_id=user_id)
        db.session.add(team)
        db.session.flush()

    already_member = TeamMember.query.filter_by(
        team_id=team.team_id,
        user_id=session['user_id']
    ).first()

    if not already_member:
        db.session.add(TeamMember(
            user_id=session['user_id'],  # accepter joins sender's team
            team_id=team.team_id
        ))

    db.session.commit()

    # accepter's team — add the sender into it
    team = Team.query.filter_by(u_id=session['user_id']).first()
    if not team:
        team = Team(u_id=session['user_id'])
        db.session.add(team)
        db.session.flush()

    already_member = TeamMember.query.filter_by(
        team_id=team.team_id,
        user_id=user_id
    ).first()

    if not already_member:
        db.session.add(TeamMember(
            user_id=user_id,  # sender joins accepter's team
            team_id=team.team_id
        ))

    db.session.commit()

    flash('Connection accepted.', 'success')

    create_notification(
        user_id=user_id,  # notify the original sender, not the accepter
        title="Connection Accepted",
        message=f"{session['user_id']} has accepted your connection request.",
        notification_type="connection"
    )

    return redirect(url_for('team.team', user_id=session['user_id']))


#reject connection request 
@connection_bp.route('/connect/reject/<int:user_id>', methods=['POST'])
def reject_connection_request(user_id):
    denied = user_required()
    if denied:
        return denied

    if session['user_id'] == user_id:
        flash('You cannot reject a connection request from yourself.', 'error')
        return redirect(url_for('user.team', user_id=user_id))

    connection = Connection.query.filter_by(
        sender_id=user_id,
        receiver_id=session['user_id']
    ).first_or_404()

    connection.status = 'rejected'
    db.session.commit()

    flash('Connection request rejected.', 'success')

    return redirect(url_for('team.team', user_id=session['user_id']))


#display all the request that user got
@connection_bp.route('/connect/requests')
def connection_requests():
    denied = user_required()
    if denied:
        return denied

    connections = Connection.query.filter_by(receiver_id=session['user_id'], status='pending').all()

    return render_template('user/connection.html', connections=connections, user=current_user)
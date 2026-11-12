from flask import Blueprint, abort, render_template, redirect, url_for, flash, session, request
from sqlalchemy import text
from app import db
from app.models import Assignee, ProjectMember, User, WorkItem, Project
from datetime import date, datetime
from app.routes.admin.admin import audit_log_action
from app.routes.user import comment
from app.routes.user.notification import create_notification
from app.routes.user.user import user_required, log_action


workitem_bp = Blueprint('workitem', __name__)

today = date.today()

@workitem_bp.route('/project/<int:p_id>/workitem')
def workitem():
    
    # Check whether user is logged in
    denied = user_required()
    if denied:
        return denied

    # Get logged-in user
    user = User.query.filter_by(user_id=session["user_id"]).first()
    
    # Get user's projects and assigned work items
    query = text("""
        SELECT
            w.work_item_id, p.p_title, w.w_title, w.u_id, a.u_id
        FROM work_items w
        JOIN projects p
            ON w.p_id = p.project_id
        LEFT JOIN assignees a
            ON w.work_item_id = a.w_id
        WHERE p.u_id = :user_id
           OR EXISTS (
                SELECT 1
                FROM work_items w2
                JOIN assignees a2
                    ON a2.w_id = w2.work_item_id
                WHERE a2.u_id = :user_id
           )
    """)

    result = db.session.execute(
        query,
        {"user_id": session["user_id"]}
    )

    work_items = result.fetchall()

    return render_template(
        'user/project.html',
        work_items=work_items
    )
    
# Add Work Item  
@workitem_bp.route('/project/<int:p_id>/workitem/add', methods=['POST'])
def add_workitem(p_id):
    denied = user_required()
    if denied:
        return denied

    u_id = session['user_id']                      # creator of the work item
    project = Project.query.get_or_404(p_id)
    membership = ProjectMember.query.filter_by(p_id=p_id, user_id=u_id).first()
    is_owner = project.u_id == u_id
    can_edit = is_owner or (membership and membership.role != 'visitor')

    # 1. permission
    if not can_edit:
        flash("You don't have permission to add work items here.", "error")
        return redirect(url_for('project.project'))


    w_title = (request.form.get('w_title') or '').strip()
    if not w_title:
        flash("Title is required.", "error")
        return redirect(url_for('project.project'))

    if WorkItem.query.filter_by(w_title=w_title, p_id=p_id).first():
        flash(f'A work item named "{w_title}" already exists in this project.', "error")
        return redirect(url_for('project.project'))

    # 3. build the work item (nothing is saved yet)
    start_date_str = request.form.get('start_date')
    deadline_str = request.form.get('deadline')

    new_work_item = WorkItem(
        w_title=w_title,
        w_des=request.form.get('w_des'),
        progress=request.form.get('progress'),
        priority=request.form.get('priority'),
        start_date=datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None,
        deadline=datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None,
        p_id=p_id,
        u_id=u_id,
    )

    db.session.add(new_work_item)
    db.session.commit()
    log_action(
        'created',
        new_work_item.w_title,
        project=project.p_title,
        p_id=p_id,
        w_id=new_work_item.work_item_id,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    
    flash(f'The "{new_work_item.w_title}" work item has been added successfully.', "success")   

    
    create_notification(
        user_id=u_id,
        title="Work Item Created",
        message=f'Work item "{new_work_item.w_title}" has been created by {session["username"]}.',
        notification_type="workitem"
    )


    return redirect(url_for('project.project'))

#Edit Work Item
@workitem_bp.route('/project/<int:p_id>/workitem/edit/<int:w_id>', methods=['POST'])
def edit_workitem(p_id, w_id):
    denied = user_required()
    if denied:
        return denied

    work_item = WorkItem.query.get_or_404(w_id)
    assignees = Assignee.query.filter_by(w_id=w_id)
    
    u_id = session['user_id']

    project = Project.query.get_or_404(p_id)
    is_owner = project.u_id == session['user_id'] 
    
    is_assignee = Assignee.query.filter_by(w_id=w_id, u_id=u_id).first() is not None
    
    is_creator = (work_item.u_id == session['user_id'] or is_assignee) and (ProjectMember.query.filter_by(p_id=p_id, user_id=u_id).first() and ProjectMember.query.filter_by(p_id=p_id, user_id=u_id).first().role != 'visitor')
    
    can_edit = is_owner or is_creator 

    if work_item.p_id != p_id:
        abort(404)
        
    if not can_edit:  # Check if the logged-in user is not a visitor
        flash("You don't have permission to edit work items here.", "error")
        return redirect(url_for('project.project'))

    if can_edit:
        if request.method == 'POST':
            new_title = (request.form.get('w_title') or '').strip()
            
            
            w_title = new_title
            
            if not w_title:
                flash("Title is required.", "error")
                return redirect(url_for('project.project'))
                
            duplicate = WorkItem.query.filter(
                WorkItem.p_id == p_id,
                WorkItem.w_title == w_title, WorkItem.work_item_id != w_id).first()
            
            
            if duplicate:
                flash(f'A work item named "{w_title}" already exists in this project.', "error")
                return redirect(url_for('project.project'))

            work_item.w_title = request.form.get('w_title')
            work_item.w_des = request.form.get('w_des')
            work_item.progress = request.form.get('progress')
            work_item.priority = request.form.get('priority')
            start_date_str = request.form.get('start_date')
            deadline_str   = request.form.get('deadline')
            work_item.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            work_item.deadline   = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

            db.session.add(work_item)
                
            db.session.commit()
            flash(f'The "{work_item.w_title}" work item has been updated successfully.', "success")
            create_notification(
                    user_id=u_id,
                    title="Work Item Updated",
                    message=f'Work item "{work_item.w_title}" has been updated by {session["username"]}.',
                    notification_type="workitem"
                )
            
            log_action(
                'edited',
                work_item.w_title,
                project=project.p_title,
                p_id=p_id,
                w_id=work_item.work_item_id,
                user_id=session.get('user_id'),
                username=session.get('username')
            )
            
            return redirect(url_for('project.project'))
                    
    return redirect(url_for('project.project'))



#Delete Work Item
@workitem_bp.route('/user/project/<int:p_id>/workitem/delete/<int:w_id>', methods=['POST'])
def delete_workitem(p_id, w_id):
    denied = user_required()
    if denied:
        return denied

    work_item = WorkItem.query.get_or_404(w_id)


    project = Project.query.get_or_404(p_id)
    is_owner = project.u_id == session['user_id'] and project.project_id == p_id
    
    is_creator = work_item.u_id == session['user_id'] and (ProjectMember.query.filter_by(p_id=p_id, user_id=session['user_id']).first() and ProjectMember.query.filter_by(p_id=p_id, user_id=session['user_id']).first().role != 'visitor')
    
    can_delete = is_owner or is_creator 
    
    if work_item.p_id != p_id:
        abort(404)
    
    w_title = work_item.w_title  # Store the title before deletion for logging and notification
    w_id = w_id  # Store the work item ID for logging
    p_id = p_id  # Store the project ID for logging
    if can_delete:  # Check if the logged-in user is not a visitor

        db.session.delete(work_item)
        db.session.commit()
        flash(f'The "{work_item.w_title}" work item has been deleted successfully.', "success")
        
        create_notification(
            user_id=session['user_id'],
            title="Work Item Deleted",
            message=f'Work item "{w_title}" has been deleted by {session["username"]}.',
            notification_type="workitem"
        )
        log_action(
            'deleted',
            w_title,
            project=project.p_title,
            p_id=p_id,
            w_id=None,
            user_id=session.get('user_id'),
            username=session.get('username')
        )
    else:
        flash("You don't have permission to delete this work item.", "error")
        
    return redirect(url_for('project.project'))

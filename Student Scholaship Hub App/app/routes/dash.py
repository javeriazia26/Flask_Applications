from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Credential, Student, Department, University, Scholarship, FundingSource, AuditLog

dash_bp = Blueprint('dash', __name__)


@dash_bp.route('/admin_dash')
def admin_dash():
    if "user_id" not in session:
        flash("Access denied!", "error")
        return redirect(url_for('auth.login'))
    else:
        user = Credential.query.filter_by(id=session['user_id']).first()
        if user.role != "admin":
            flash("Access denied!", "error")
            return redirect(url_for('dash.user_dash'))
    
    students = Student.query.count()
    departments = Department.query.count()
    scholarships = Scholarship.query.count()
    funding_sources = FundingSource.query.count()
    audit_logs = AuditLog.query.order_by(AuditLog.date.desc(), 
                AuditLog.time.desc()).limit(10).all()
    
    return render_template('admin/admin_dash.html', 
        all_students=students,
        all_departments=departments,
        all_scholarships=scholarships,
        all_fund_src=funding_sources,
        all_audit_logs=audit_logs       
                           
        )

from flask import session, flash, redirect, url_for
from app.models import Credential


@dash_bp.route('/user_dash')
def user_dash():
    if "user_id" not in session:
        flash("Access denied!", "error")
        return redirect(url_for('auth.login'))

    user = Credential.query.filter_by(id=session['user_id']).first()

    # get filter values from URL
    selected_campus = request.args.get('c_name')
    selected_dept   = request.args.get('d_name')
     
    # for dropdowns
    all_universities = University.query.all()
    if selected_campus:
        departments = Department.query.filter_by(c_name=selected_campus).all()
    else:
        departments = []



    # build student query with filters
    query = Student.query

    if selected_campus:
        dept_ids = [d.d_id for d in Department.query.filter_by(c_name=selected_campus).all()]
        query = query.filter(Student.d_id.in_(dept_ids))

    if selected_dept:
        dept_ids = [d.d_id for d in Department.query.filter_by(d_name=selected_dept).all()]
        query = query.filter(Student.d_id.in_(dept_ids))

    students = query.all()

    return render_template('user_dash.html',
        username=user.username,
        universities=all_universities,
        departments=departments,
        students=students,
        selected_campus=selected_campus,
        selected_dept=selected_dept
    )
    
    
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Student, Scholarship, Department
from app.routes.admin.admin import admin_required, log_action   # shared helper
from datetime import datetime
from app.services.encryption_service import encrypt_data, hash_data, decrypt_data

std_bp = Blueprint('student', __name__)


# List all students
@std_bp.route('/admin/std')
def std():
    denied = admin_required()
    if denied:
        return denied

    all_students     = Student.query.all()
    all_departments  = Department.query.all()
    all_scholarships = Scholarship.query.all()
    
    edit_id = request.args.get('edit')
    editing_student = None
    if edit_id:
        editing_student = Student.query.get(edit_id)

        editing_student.display_cnic = decrypt_data(editing_student.encrypted_cnic)
        editing_student.display_std_phone_no = decrypt_data(editing_student.encrypted_phone)

    return render_template('admin/std.html',
        students=all_students,
        departments=all_departments,
        scholarships=all_scholarships,
        editing_student=editing_student
    )


# Add Student
@std_bp.route('/admin/std/add', methods=['POST'])
def add_std():
    denied = admin_required()
    if denied:
        return denied

    first_name     = request.form.get('first_name')
    last_name      = request.form.get('last_name')
    cnic           = request.form.get('cnic')
    gender         = request.form.get('gender')
    std_phone_no   = request.form.get('std_phone_no')
    program        = request.form.get('program')
    admission_date_str = request.form.get('admission_date')
    semester       = request.form.get('semester')
    s_id           = request.form.get('s_id')
    d_id           = request.form.get('d_id')
    
    admission_date = datetime.strptime(admission_date_str, '%Y-%m-%d').date() if admission_date_str else None
    
    encrypted_cnic = encrypt_data(cnic)
    cnic_hash = hash_data(cnic)

    encrypted_phone = encrypt_data(std_phone_no)
    phone_hash = hash_data(std_phone_no)

    #for cnic
    existing_student = Student.query.filter_by(cnic_hash=cnic_hash).first()
    if existing_student:
        flash(f"A student with this CNIC already exists in the system.", "error")
        return redirect(url_for('student.std'))
    
    #for phone
    existing_student = Student.query.filter_by(phone_hash=phone_hash).first()
    if existing_student:
        flash(f"A student with this phone number already exists in the system.", "error")
        return redirect(url_for('student.std'))

    new_student = Student(
        first_name     = first_name,
        last_name      = last_name,
        encrypted_cnic=encrypted_cnic,
        cnic_hash=cnic_hash,

        gender         = gender,
        encrypted_phone=encrypted_phone,
        phone_hash=phone_hash,
        
        program        = program,
        admission_date = admission_date,
        semester       = semester,
        s_id           = s_id,
        d_id           = d_id
        
    )

    db.session.add(new_student)
    db.session.commit()
    log_action('Added', 'Student')
    
    flash(f"Student '{first_name} {last_name}' has been enrolled successfully.", "success")
    return redirect(url_for('student.std'))


# Edit Student
@std_bp.route('/admin/std/edit/<int:std_id>', methods=['GET', 'POST'])
def edit_std(std_id):
    denied = admin_required()
    if denied:
        return denied

    student    = Student.query.get_or_404(std_id)
    scholarship = Scholarship.query.all()
    department  = Department.query.all()


    if request.method == 'POST':
        
        student.first_name     = request.form.get('first_name')
        student.last_name      = request.form.get('last_name')
        cnic           = request.form.get('cnic')
        
        student.gender         = request.form.get('gender')
        student.program        = request.form.get('program')
        std_phone_no   = request.form.get('std_phone_no')
        
        admission_date_str = request.form.get('admission_date')
        student.semester       = request.form.get('semester')
        student.s_id           = request.form.get('s_id')
        student.d_id           = request.form.get('d_id')

        student.admission_date = datetime.strptime(admission_date_str, '%Y-%m-%d').date() if admission_date_str else None
       
        #for cnic 
        encrypted_cnic = encrypt_data(cnic)
        cnic_hash = hash_data(cnic)  
        student.cnic_hash = cnic_hash
            
        existing_student = Student.query.filter(
            Student.cnic_hash == cnic_hash,
            Student.std_id != student.std_id).first()
    
        if existing_student:
            flash("A student with this CNIC already exists.", "error")
            return redirect(url_for("student.std"))
        
        student.encrypted_cnic = encrypted_cnic
        student.cnic_hash = cnic_hash
        
        #for phone
        encrypted_phone = encrypt_data(std_phone_no)
        phone_hash = hash_data(std_phone_no) 
        student.phone_hash = phone_hash
    
        existing_student = Student.query.filter(
            Student.phone_hash == student.phone_hash,
            Student.std_id != student.std_id).first()
    
        if existing_student:
            flash("A student with this phone number already exists.", "error")
            return redirect(url_for("student.std"))
        
        student.encrypted_phone = encrypted_phone
        student.phone_hash = phone_hash
        
        db.session.commit()
        log_action('Updated', 'Student')
        flash(f"'{student.first_name} {student.last_name}' record has been updated successfully.", "success")
        return redirect(url_for('student.std'))


    return redirect(url_for('student.std'))


# Delete Student
@std_bp.route('/admin/std/delete/<int:std_id>', methods=['POST'])
def delete_std(std_id):
    
    denied = admin_required()
    if denied:
        return denied

    student = Student.query.get_or_404(std_id)
    
    # save name before deleting
    full_name = f"{student.first_name} {student.last_name}"
    
    db.session.delete(student)
    db.session.commit()
    log_action('Deleted', 'Student')
    
    flash(f"'{full_name}' has been removed from the system.", "success")
    return redirect(url_for('student.std'))

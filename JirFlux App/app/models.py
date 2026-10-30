from app import db
from werkzeug.security import generate_password_hash, check_password_hash

#Credentials
class Credential(db.Model):
    __tablename__ = "credential"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.String(20), default="student")
    verified = db.Column(db.Boolean, default=False)
    hashed_password = db.Column(db.String(200), nullable=False)
    
    emailotps = db.relationship("EmailOTP", backref="credential", lazy=True)
    
    otp_resend_count = db.Column(db.Integer, default=0)  #max 2
    otp_last_resend_date = db.Column(db.Date, nullable=True)
    
    
#Tokens   
class EmailOTP(db.Model):
    __tablename__ = "email_otp"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("credential.id"), nullable = False)
    hashed_otp = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # or "password_reset"
    attempts = db.Column(db.Integer, default=0)      #max 5

    
#Audit Logs
class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    username = db.Column(db.String(30), nullable=False)
    action   = db.Column(db.String(100), nullable=False)
    entity   = db.Column(db.String(50), nullable=False)

    user_id  = db.Column(db.Integer, db.ForeignKey("credential.id"), nullable=False)

# Funding Source
class FundingSource(db.Model):
    __tablename__ = "funding_source"

    f_source_id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(100), nullable=False)
    phone_no = db.Column(db.String(20), unique=True)
    email_id = db.Column(db.String(20), unique=True)
    type = db.Column(db.String(20),nullable=False)

    scholarships = db.relationship("Scholarship", backref="funding_source", lazy=True)

# Scholarship
class Scholarship(db.Model):
    __tablename__ = "scholarship"

    s_id = db.Column(db.Integer, primary_key=True)
    s_name = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date)
    total_amount = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.Date)
    fund_type = db.Column(db.String(20), nullable=False)

    f_source_id = db.Column(
        db.Integer,
        db.ForeignKey("funding_source.f_source_id"),
        nullable=False
    )

    students = db.relationship("Student", backref="scholarship", lazy=True)

# University
class University(db.Model):
    __tablename__ = "university"

    uni_id = db.Column(db.Integer, primary_key=True)
    uni_name = db.Column(db.String(20), nullable=False)
    c_name = db.Column(db.String(20), nullable=False, unique=True)
    uni_phone_no = db.Column(db.String(20), nullable=False)
    uni_location = db.Column(db.String(20), nullable=False, unique=True)

    departments = db.relationship("Department", backref="university", lazy=True)

# Department
class Department(db.Model):
    __tablename__ = "department"

    d_id = db.Column(db.Integer, primary_key=True)
    d_name = db.Column(db.String(100), nullable=False)
    c_name = db.Column(db.String(20),nullable=False)

    uni_id = db.Column(
        db.Integer,
        db.ForeignKey("university.uni_id"),
        nullable=False
    )

    students = db.relationship("Student", backref="department", lazy=True)

# Student
class Student(db.Model):
    __tablename__ = "student"

    __table_args__ = (
    db.UniqueConstraint(
        "cnic_hash",
        name="uq_student_cnic_hash"
    ),
    db.UniqueConstraint(
        "phone_hash",
        name="uq_student_phone_hash"
    ),
)

    
    std_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    
    encrypted_cnic = db.Column(db.String(500))
    cnic_hash = db.Column(db.String(64))
    
    gender = db.Column(db.String(20))
    
    
    encrypted_phone = db.Column(db.String(500))
    phone_hash = db.Column(db.String(64))

    program = db.Column(db.String(20), nullable=False)
    admission_date = db.Column(db.Date)
    semester = db.Column(db.Integer)

    s_id = db.Column(
        db.Integer,
        db.ForeignKey("scholarship.s_id"),
        nullable=False
    )

    d_id = db.Column(
        db.Integer,
        db.ForeignKey("department.d_id"),
        nullable=False
    )

    results = db.relationship("Result", backref="student", lazy=True)

# Result
class Result(db.Model):
    __tablename__ = "result"

    r_id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, nullable=False)

    std_id = db.Column(
        db.Integer,
        db.ForeignKey("student.std_id"),
        nullable=False
    )
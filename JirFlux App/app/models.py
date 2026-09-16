from datetime import datetime
from app import db


# =========================================================
# USER
# =========================================================

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(50), nullable=True)
    pass_hash = db.Column(db.String(255), nullable=False)
    email_id = db.Column(db.String(255), unique=True, nullable=False)
    phone_hash = db.Column(db.String(255), unique=True, nullable=True)
    phone_encrypt = db.Column(db.Text, nullable=True)
    
    u_title = db.Column(db.String(100), nullable=True)
    picture = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    u_role = db.Column(db.String(30), default="user", nullable=False)
    location = db.Column(db.String(100), nullable=True)
    
    verified = db.Column(db.Boolean, default=False, nullable=False)
    
    password_attempt = db.Column(db.Integer, default=0, nullable=False)
    otp_resend_count = db.Column(db.Integer, default=0, nullable=False)
    otp_lock_until = db.Column(db.DateTime, nullable=True)
    account_lock_until = db.Column(db.DateTime, nullable=True)
    
    two_factor_enabled = db.Column(db.Boolean,default=False,nullable=False)
    phone_verified = db.Column(db.Boolean, default=False,nullable=False)
    account_notifications = db.Column(db.Boolean,default=True,nullable=False)
    security_notifications = db.Column(db.Boolean,default=True,nullable=False)

    totp_secret = db.Column(db.Text, nullable=True)
    
    # Relationships
    otps = db.relationship("OTP", back_populates="user", cascade="all, delete-orphan")

    owned_projects = db.relationship(
        "Project",
        back_populates="owner",
        foreign_keys="Project.u_id"
    )

    created_work_items = db.relationship(
        "WorkItem",
        back_populates="creator",
        foreign_keys="WorkItem.u_id"
    )

    assignments = db.relationship(
        "Assignee",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    comments = db.relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    files = db.relationship(
        "File",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    sent_connections = db.relationship(
        "Connection",
        foreign_keys="Connection.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )

    received_connections = db.relationship(
        "Connection",
        foreign_keys="Connection.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )

    created_team = db.relationship(
        "Team",
        back_populates="creator",
        uselist=False
    )

    team_memberships = db.relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    project_memberships = db.relationship(
        "ProjectMember",
        foreign_keys="ProjectMember.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    project_invitations_sent = db.relationship(
        "ProjectMember",
        foreign_keys="ProjectMember.invited_by",
        back_populates="inviter"
    )
    
    skills = db.relationship(
    "Skill",
    back_populates="user",
    cascade="all, delete-orphan"
    )
    
    trusted_devices = db.relationship(
    "TrustedDevice",
    back_populates="user",
    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"
    
# =========================================================
# TRUSTED DEVICE
# =========================================================
   

class TrustedDevice(db.Model):
    __tablename__ = "trusted_devices"

    device_id = db.Column(db.Integer, primary_key=True)

    u_id = db.Column(db.Integer,db.ForeignKey("users.user_id"),nullable=False)
    device_token_hash = db.Column(db.String(255),nullable=False)

    device_name = db.Column(db.String(100), nullable=False, default="Unknown Device")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    
    user = db.relationship("User", back_populates="trusted_devices")

# =========================================================
# SKILLS
# =========================================================

class Skill(db.Model):
    __tablename__ = "skills"

    skill_id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=True)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    
    user = db.relationship("User", back_populates="skills")
    
# =========================================================
# OTP
# =========================================================

class OTP(db.Model):
    __tablename__ = "otps"

    otp_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.String(50), nullable=False)
    otp_attempt = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="otps")

    def __repr__(self):
        return f"<OTP {self.otp_id}>"


# =========================================================
# AUDIT LOG
# =========================================================

class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)


# =========================================================
# ITEM LOG
# =========================================================

class ItemLog(db.Model):
    __tablename__ = "item_log"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    project = db.Column(db.String(50), nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    w_id = db.Column(db.Integer, db.ForeignKey("work_items.work_item_id"), nullable=False)


# =========================================================
# PROJECT
# =========================================================

class Project(db.Model):
    __tablename__ = "projects"

    project_id = db.Column(db.Integer, primary_key=True)
    p_title = db.Column(db.String(150), nullable=False)
    p_des = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    current_status = db.Column(db.String(50), nullable=False, default="Not Started")
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)  # owner

    owner = db.relationship(
        "User",
        back_populates="owned_projects",
        foreign_keys=[u_id]
    )

    work_items = db.relationship(
        "WorkItem",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    members = db.relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project {self.p_title}>"


# =========================================================
# WORK ITEM
# =========================================================

class WorkItem(db.Model):
    __tablename__ = "work_items"

    work_item_id = db.Column(db.Integer, primary_key=True)
    w_title = db.Column(db.String(150), nullable=False, unique=True)
    w_des = db.Column(db.Text, nullable=True)
    progress = db.Column(db.String(20), default="Not Started", nullable=False)
    priority = db.Column(db.String(30), nullable=False, default="Medium")
    deadline = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    p_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)  # creator

    project = db.relationship("Project", back_populates="work_items")

    creator = db.relationship(
        "User",
        back_populates="created_work_items",
        foreign_keys=[u_id]
    )

    assignees = db.relationship(
        "Assignee",
        back_populates="work_item",
        cascade="all, delete-orphan"
    )

    comments = db.relationship(
        "Comment",
        back_populates="work_item",
        cascade="all, delete-orphan"
    )

    files = db.relationship(
        "File",
        back_populates="work_item",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<WorkItem {self.w_title}>"


# =========================================================
# ASSIGNEE
# =========================================================

class Assignee(db.Model):
    __tablename__ = "assignees"

    assignee_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False) # assignee
    w_id = db.Column(db.Integer, db.ForeignKey("work_items.work_item_id"), nullable=False) #specific work item

    __table_args__ = (
        db.UniqueConstraint("u_id", "w_id", name="uq_user_work_item_assignment"),
    )

    user = db.relationship("User", back_populates="assignments")
    work_item = db.relationship("WorkItem", back_populates="assignees")

    def __repr__(self):
        return f"<Assignee {self.assignee_id}>"


# =========================================================
# COMMENT
# =========================================================

class Comment(db.Model):
    __tablename__ = "comments"

    comment_id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    c_upload_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    w_id = db.Column(db.Integer, db.ForeignKey("work_items.work_item_id"), nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    work_item = db.relationship("WorkItem", back_populates="comments")
    user = db.relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment {self.comment_id}>"


# =========================================================
# FILE
# =========================================================

class File(db.Model):
    __tablename__ = "files"

    file_id = db.Column(db.Integer, primary_key=True)
    f_title = db.Column(db.String(255), nullable=False)
    f_type = db.Column(db.String(100), nullable=False)
    f_size = db.Column(db.BigInteger, nullable=False)
    f_upload_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    w_id = db.Column(db.Integer, db.ForeignKey("work_items.work_item_id"), nullable=False)

    user = db.relationship("User", back_populates="files")
    work_item = db.relationship("WorkItem", back_populates="files")

    def __repr__(self):
        return f"<File {self.f_title}>"


# =========================================================
# NOTIFICATION
# =========================================================

class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True)
    n_title = db.Column(db.String(150), nullable=False)
    n_des = db.Column(db.Text, nullable=True)
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    n_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notification_type = db.Column(db.String(50), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="notifications")
    
    account_notifications = db.Column(db.Boolean,default=True,nullable=False)
    security_notifications = db.Column(db.Boolean,default=True,nullable=False)
    
    
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)
    due_date_reminders = db.Column(db.Boolean, default=True, nullable=False)
    mentions_comments = db.Column(db.Boolean, default=True, nullable=False)
    team_updates = db.Column(db.Boolean, default=False, nullable=False)
    weekly_summary = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Notification {self.notification_id}>"


# =========================================================
# CONNECTION
# =========================================================

class Connection(db.Model):
    __tablename__ = "connection"

    connection_id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_connections"
    )

    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_connections"
    )

    def __repr__(self):
        return f"<Connection {self.connection_id}>"


# =========================================================
# TEAM
# =========================================================

class Team(db.Model):
    __tablename__ = "team"

    team_id = db.Column(db.Integer, primary_key=True)

    # One user can create only one team
    u_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship(
        "User",
        foreign_keys=[u_id],
        back_populates="created_team"
    )

    members = db.relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Team {self.team_id}>"


# =========================================================
# TEAM MEMBER
# =========================================================

class TeamMember(db.Model):
    __tablename__ = "team_member"

    team_member_id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.team_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )

    team = db.relationship("Team", back_populates="members")
    user = db.relationship("User", back_populates="team_memberships")

    def __repr__(self):
        return f"<TeamMember {self.team_member_id}>"


# =========================================================
# PROJECT MEMBER
# =========================================================

class ProjectMember(db.Model):
    __tablename__ = "project_member"

    project_member_id = db.Column(db.Integer, primary_key=True)
    p_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    role = db.Column(db.String(50), nullable=True, default="Member")
    status = db.Column(db.String(20), nullable=False, default="pending")
    invited_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("p_id", "user_id", name="uq_project_user"),
    )

    project = db.relationship("Project", back_populates="members")

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="project_memberships"
    )

    inviter = db.relationship(
        "User",
        foreign_keys=[invited_by],
        back_populates="project_invitations_sent"
    )

    def __repr__(self):
        return f"<ProjectMember {self.project_member_id}>"

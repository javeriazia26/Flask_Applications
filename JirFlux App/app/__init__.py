import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

load_dotenv()

# 1. Create db FIRST
db = SQLAlchemy()
migrate = Migrate()

# 2. Import models SECOND (now db exists, so models.py's "from app import db" works)
from app import models


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)

    #authorization
    from app.routes.auth.auth import auth_bp
    from app.routes.auth.verify import verify_bp
    from app.routes.auth.forget_pass import forget_pass_bp
    from app.routes.auth.login_form import login_form_bp
    from app.routes.auth.forget_pass import forget_pass_bp
    from app.routes.auth.reg_form import reg_form_bp
    
    #admin
    from app.routes.admin.admin import admin_bp
    from app.routes.admin.audit_log import audit_log_bp
    from app.routes.admin.admin_profile import admin_profile_bp
    from app.routes.admin.admin_setting import admin_settings_bp
    
    #user
    from app.routes.user.dash import dash_bp
    from app.routes.user.connection import connection_bp
    from app.routes.user.project import project_bp
    from app.routes.user.profile import profile_bp
    from app.routes.user.project_member import project_member_bp
    from app.routes.user.task import task_bp
    from app.routes.user.workitem import workitem_bp
    from app.routes.user.user import user_bp
    from app.routes.user.notification import notification_bp
    from app.routes.user.setting import settings_bp
    from app.routes.user.team import team_bp
    
    #user
    app.register_blueprint(project_bp)
    app.register_blueprint(project_member_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(workitem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(connection_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(team_bp)

    #authorization
    app.register_blueprint(verify_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(forget_pass_bp)
    app.register_blueprint(login_form_bp)
    app.register_blueprint(reg_form_bp)
    
    #admin
    app.register_blueprint(audit_log_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_profile_bp)
    app.register_blueprint(admin_settings_bp)
    
    
    return app  

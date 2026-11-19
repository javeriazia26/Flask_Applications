import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth


load_dotenv()

# 1. Create db FIRST
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()

# 2. Import models SECOND (now db exists, so models.py's "from app import db" works)
from app import models


def create_app():
    
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    
    app.config.from_object("config.Config")
    oauth.init_app(app)
    
   

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        }
    )

    #authorization
    from app.routes.auth.auth import auth_bp
    from app.routes.auth.verify import verify_bp
    from app.routes.auth.google_auth import google_auth_bp
    
    from app.routes.auth.login_form import login_form_bp
    from app.routes.auth.set_pass import set_pass_bp
    from app.routes.auth.reg_form import reg_form_bp
    
    #admin
    from app.routes.admin.admin import admin_bp
    from app.routes.admin.audit_log import audit_log_bp
    from app.routes.admin.admin_profile import admin_profile_bp
    from app.routes.admin.admin_settings import admin_settings_bp
    
    
    #user
    from app.routes.user.dash import dash_bp
    from app.routes.user.connection import connection_bp
    from app.routes.user.task import task_bp
    from app.routes.user.calender import calendar_bp
    from app.routes.user.avatar import avatar_bp
    
    from app.routes.user.project import project_bp
    from app.routes.user.project_member import project_member_bp
    
    from app.routes.user.workitem import workitem_bp
    from app.routes.user.assignee import assignee_bp
    
    from app.routes.user.user import user_bp
    from app.routes.user.notification import notification_bp
    from app.routes.user.team import team_bp
    from app.routes.user.profile import profile_bp
    from app.routes.user.settings import settings_bp
    from app.routes.user.comment import comment_bp
    
    from app.routes.user.attachment import attachment_bp
    
    
    #user
    app.register_blueprint(project_bp)
    app.register_blueprint(project_member_bp)
    app.register_blueprint(task_bp)
    
    app.register_blueprint(calendar_bp)
    app.register_blueprint(workitem_bp)
    app.register_blueprint(assignee_bp)
    
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)
    
    app.register_blueprint(connection_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(attachment_bp)
    app.register_blueprint(avatar_bp)


    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)

    #authorization
    app.register_blueprint(verify_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_auth_bp)
    
    app.register_blueprint(set_pass_bp)
    app.register_blueprint(login_form_bp)
    app.register_blueprint(reg_form_bp)
    
    #admin
    app.register_blueprint(audit_log_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_profile_bp)
    app.register_blueprint(admin_settings_bp)
    

    return app  

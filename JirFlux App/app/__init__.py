import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config


db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    
    db.init_app(app)
    migrate.init_app(app, db)

    from app import models

    from app.routes.auth import auth_bp
    from app.routes.dash import dash_bp
    from app.routes.reg_form import reg_form_bp
    from app.routes.login_form import login_form_bp
    from app.routes.verify import verify_bp
    from app.routes.forget_pass import forget_pass_bp
    
    #admin folder
    from app.routes.admin.admin import admin_bp
    from app.routes.admin.audit_log import audit_log_bp
    from app.routes.admin.depart import depart_bp
    from app.routes.admin.fund_src import fund_src_bp
    from app.routes.admin.result import result_bp
    from app.routes.admin.scholar import scholar_bp
    from app.routes.admin.std import std_bp
    from app.routes.admin.uni import uni_bp
    from app.routes.forget_pass import forget_pass_bp
    

    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(reg_form_bp)
    app.register_blueprint(login_form_bp)
    app.register_blueprint(verify_bp)  
    app.register_blueprint(forget_pass_bp)
    
    #admin folder
    app.register_blueprint(admin_bp)
    app.register_blueprint(audit_log_bp)
    app.register_blueprint(depart_bp)
    app.register_blueprint(fund_src_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(scholar_bp)
    app.register_blueprint(std_bp)
    app.register_blueprint(uni_bp)
    
    return app  
from flask import Blueprint
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
from flask_wtf import FlaskForm


login_form_bp = Blueprint('login_form', __name__)
email_pattern = Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message="Please Enter valid email address")
class loginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), email_pattern])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Login")
    

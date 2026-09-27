from flask import Blueprint
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
from flask_wtf import FlaskForm
from secrets import token_urlsafe

reg_form_bp = Blueprint('reg_form', __name__)

email_pattern = Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message = "Please enter valid email address.")

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Regexp(r'^[A-Za-z0-9_]{3,20}$', message="Username must be 3-20 characters, letters/numbers/underscore only")
    ])
    email = StringField("Email", validators=[DataRequired(), email_pattern])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")
    token = token_urlsafe(32)

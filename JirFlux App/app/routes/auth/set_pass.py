from flask import Blueprint
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp
from flask_wtf import FlaskForm


set_pass_bp = Blueprint('set_pass', __name__)

class EmailForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message="Please enter a valid email address.")])
    submit = SubmitField("Submit")

class SetPasswordForm(FlaskForm):
    password = StringField("New Password", validators=[DataRequired()])
    confirm_password = StringField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Set Password")
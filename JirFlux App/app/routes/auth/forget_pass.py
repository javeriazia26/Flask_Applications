from flask import Blueprint
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp
from flask_wtf import FlaskForm


forget_pass_bp = Blueprint('forget_pass', __name__)

class ForgetPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message="Please enter a valid email address.")])
    submit = SubmitField("Submit")

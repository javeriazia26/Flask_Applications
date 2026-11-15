from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

class GoogleLinkForm(FlaskForm):
    password = PasswordField(
        "JIRFLUX Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Verify and Link Google")
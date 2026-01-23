"""Authentication forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import Usuario


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField(
        'Usuario',
        validators=[DataRequired(message='Ingrese su usuario')]
    )
    password = PasswordField(
        'Contraseña',
        validators=[DataRequired(message='Ingrese su contraseña')]
    )
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Ingresar')


class ChangePasswordForm(FlaskForm):
    """Change password form."""

    current_password = PasswordField(
        'Contraseña Actual',
        validators=[DataRequired(message='Ingrese su contraseña actual')]
    )
    new_password = PasswordField(
        'Nueva Contraseña',
        validators=[
            DataRequired(message='Ingrese la nueva contraseña'),
            Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
        ]
    )
    confirm_password = PasswordField(
        'Confirmar Contraseña',
        validators=[
            DataRequired(message='Confirme la nueva contraseña'),
            EqualTo('new_password', message='Las contraseñas no coinciden')
        ]
    )
    submit = SubmitField('Cambiar Contraseña')


class SelectEmpresaForm(FlaskForm):
    """Select company form."""

    empresa_id = SelectField(
        'Empresa',
        coerce=int,
        validators=[DataRequired(message='Seleccione una empresa')]
    )
    submit = SubmitField('Seleccionar')

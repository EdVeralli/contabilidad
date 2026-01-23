"""Cuentas forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import Plan


class CuentaForm(FlaskForm):
    """Form for creating/editing an account."""

    cuenta = StringField(
        'Codigo de Cuenta',
        validators=[
            DataRequired(message='El codigo de cuenta es requerido'),
            Length(max=10, message='Maximo 10 caracteres')
        ]
    )
    nombre = StringField(
        'Nombre',
        validators=[
            DataRequired(message='El nombre es requerido'),
            Length(max=60, message='Maximo 60 caracteres')
        ]
    )
    nivel = SelectField(
        'Nivel',
        coerce=int,
        choices=[(i, str(i)) for i in range(1, 10)],
        default=1
    )
    imputable = SelectField(
        'Imputable',
        choices=[('N', 'No'), ('S', 'Si')],
        default='N'
    )
    monetaria = SelectField(
        'Monetaria',
        choices=[('N', 'No'), ('S', 'Si')],
        default='N'
    )
    ajustable = SelectField(
        'Ajustable',
        choices=[('N', 'No'), ('S', 'Si')],
        default='N'
    )
    tipo_saldo = SelectField(
        'Tipo de Saldo',
        choices=[('D', 'Deudor'), ('A', 'Acreedor')],
        default='D'
    )
    activa = BooleanField('Activa', default=True)
    submit = SubmitField('Guardar')

    def __init__(self, empresa_id, original_cuenta=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa_id = empresa_id
        self.original_cuenta = original_cuenta

    def validate_cuenta(self, field):
        """Validate account code is unique within the company."""
        # Skip validation if code hasn't changed
        if self.original_cuenta and field.data == self.original_cuenta:
            return

        existing = Plan.query.filter_by(
            empresa_id=self.empresa_id,
            cuenta=field.data
        ).first()

        if existing:
            raise ValidationError('Ya existe una cuenta con este codigo.')


class BusquedaCuentaForm(FlaskForm):
    """Form for searching accounts."""

    q = StringField('Buscar', validators=[Optional()])
    nivel = SelectField(
        'Nivel',
        coerce=int,
        choices=[(0, 'Todos')] + [(i, str(i)) for i in range(1, 10)],
        default=0
    )
    imputable = SelectField(
        'Imputable',
        choices=[('', 'Todos'), ('S', 'Si'), ('N', 'No')],
        default=''
    )
    activa = SelectField(
        'Estado',
        choices=[('', 'Todos'), ('1', 'Activas'), ('0', 'Inactivas')],
        default='1'
    )
    submit = SubmitField('Buscar')

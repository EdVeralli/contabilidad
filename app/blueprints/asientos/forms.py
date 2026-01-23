"""Asientos forms."""
from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, BooleanField, SubmitField,
    TextAreaField, FieldList, FormField, DecimalField, HiddenField
)
from wtforms.validators import DataRequired, Optional, NumberRange


class AsientoLineaForm(FlaskForm):
    """Form for a single journal entry line."""

    class Meta:
        csrf = False

    cuenta_id = HiddenField('Cuenta ID')
    cuenta_codigo = StringField('Cuenta', validators=[Optional()])
    debe = DecimalField('Debe', places=2, default=0, validators=[Optional()])
    haber = DecimalField('Haber', places=2, default=0, validators=[Optional()])
    leyenda = StringField('Leyenda', validators=[Optional()])


class AsientoForm(FlaskForm):
    """Form for creating/editing a journal entry."""

    fecha = DateField(
        'Fecha',
        validators=[DataRequired(message='La fecha es requerida')],
        default=date.today
    )
    leyenda_global = TextAreaField('Leyenda Global', validators=[Optional()])
    es_apertura = BooleanField('Asiento de Apertura', default=False)
    submit = SubmitField('Guardar')


class BusquedaAsientoForm(FlaskForm):
    """Form for searching journal entries."""

    fecha_desde = DateField('Desde', validators=[Optional()])
    fecha_hasta = DateField('Hasta', validators=[Optional()])
    numero = StringField('Numero', validators=[Optional()])
    cuenta = StringField('Cuenta', validators=[Optional()])
    leyenda = StringField('Leyenda', validators=[Optional()])
    submit = SubmitField('Buscar')

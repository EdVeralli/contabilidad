"""Empresa model."""
from datetime import datetime
from app.extensions import db


class Empresa(db.Model):
    """Model for company/business entity."""

    __tablename__ = 'empresa'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    comentario = db.Column(db.String(200))
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    usuarios = db.relationship('Usuario', backref='empresa', lazy='dynamic')
    planes = db.relationship('Plan', backref='empresa', lazy='dynamic')
    asientos = db.relationship('Asiento', backref='empresa', lazy='dynamic')
    saldos = db.relationship('Saldo', backref='empresa', lazy='dynamic')
    ejercicios = db.relationship('Ejercicio', backref='empresa', lazy='dynamic')
    tablas_inflacion = db.relationship('TablaInflacion', backref='empresa', lazy='dynamic')

    def __repr__(self):
        return f'<Empresa {self.codigo}: {self.nombre}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'comentario': self.comentario,
            'activa': self.activa
        }

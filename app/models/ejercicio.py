"""Ejercicio (Fiscal Year) model."""
from app.extensions import db


class Ejercicio(db.Model):
    """Model for fiscal year/accounting period."""

    __tablename__ = 'ejercicio'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    anio = db.Column(db.SmallInteger, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    cerrado = db.Column(db.Boolean, default=False)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'anio', name='uk_empresa_anio'),
    )

    def fecha_en_ejercicio(self, fecha):
        """Check if a date falls within this fiscal year."""
        return self.fecha_inicio <= fecha <= self.fecha_fin

    def __repr__(self):
        return f'<Ejercicio {self.anio} ({self.fecha_inicio} - {self.fecha_fin})>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'anio': self.anio,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'cerrado': self.cerrado
        }

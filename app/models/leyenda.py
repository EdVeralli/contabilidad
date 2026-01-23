"""Leyenda (Predefined Description) model."""
from app.extensions import db


class Leyenda(db.Model):
    """Model for predefined journal entry descriptions."""

    __tablename__ = 'leyenda'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    codigo = db.Column(db.String(10), nullable=False)
    descripcion = db.Column(db.String(100), nullable=False)
    activa = db.Column(db.Boolean, default=True)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'codigo', name='uk_empresa_leyenda'),
    )

    def __repr__(self):
        return f'<Leyenda {self.codigo}: {self.descripcion}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'activa': self.activa
        }

"""AsientoTipo (Journal Entry Template) models."""
from app.extensions import db


class AsientoTipo(db.Model):
    """Model for journal entry templates."""

    __tablename__ = 'asiento_tipo'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    titulo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True)

    # Relationships
    lineas = db.relationship(
        'AsientoTipoLinea',
        backref='asiento_tipo',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='AsientoTipoLinea.item'
    )

    def __repr__(self):
        return f'<AsientoTipo {self.titulo}>'

    def to_dict(self, include_lineas=False):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'activo': self.activo
        }
        if include_lineas:
            data['lineas'] = [linea.to_dict() for linea in self.lineas]
        return data


class AsientoTipoLinea(db.Model):
    """Model for journal entry template detail line."""

    __tablename__ = 'asiento_tipo_linea'

    id = db.Column(db.Integer, primary_key=True)
    asiento_tipo_id = db.Column(
        db.Integer,
        db.ForeignKey('asiento_tipo.id', ondelete='CASCADE'),
        nullable=False
    )
    item = db.Column(db.SmallInteger, nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    tipo_movimiento = db.Column(db.String(1), nullable=False)  # D/H
    leyenda = db.Column(db.String(50))

    # Relationship
    cuenta = db.relationship('Plan')

    def __repr__(self):
        return f'<AsientoTipoLinea {self.item}: {self.tipo_movimiento}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'asiento_tipo_id': self.asiento_tipo_id,
            'item': self.item,
            'cuenta_id': self.cuenta_id,
            'cuenta_codigo': self.cuenta.cuenta if self.cuenta else None,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'tipo_movimiento': self.tipo_movimiento,
            'leyenda': self.leyenda
        }

"""Asiento (Journal Entry) models."""
from datetime import datetime
from enum import Enum
from app.extensions import db


class EstadoAsiento(str, Enum):
    """Enum for journal entry status."""
    ACTIVO = 'ACTIVO'
    ANULADO = 'ANULADO'


class Asiento(db.Model):
    """Model for journal entry header."""

    __tablename__ = 'asiento'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False, index=True)  # nucontrol
    fecha = db.Column(db.Date, nullable=False, index=True)
    es_apertura = db.Column(db.Boolean, default=False)
    leyenda_global = db.Column(db.String(200))
    estado = db.Column(db.Enum(EstadoAsiento), default=EstadoAsiento.ACTIVO)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    anulado_at = db.Column(db.DateTime)
    anulado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    # Unique constraint for empresa + numero
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'numero', name='uk_empresa_numero'),
    )

    # Relationships
    lineas = db.relationship(
        'AsientoLinea',
        backref='asiento',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='AsientoLinea.item'
    )
    usuario_anulador = db.relationship(
        'Usuario',
        foreign_keys=[anulado_por],
        backref='asientos_anulados'
    )

    @property
    def is_activo(self):
        """Check if entry is active."""
        return self.estado == EstadoAsiento.ACTIVO

    @property
    def total_debe(self):
        """Calculate total debit."""
        return sum(linea.debe or 0 for linea in self.lineas)

    @property
    def total_haber(self):
        """Calculate total credit."""
        return sum(linea.haber or 0 for linea in self.lineas)

    @property
    def esta_balanceado(self):
        """Check if entry is balanced."""
        return abs(self.total_debe - self.total_haber) < 0.01

    def anular(self, usuario_id):
        """Mark entry as void."""
        self.estado = EstadoAsiento.ANULADO
        self.anulado_at = datetime.utcnow()
        self.anulado_por = usuario_id

    def __repr__(self):
        return f'<Asiento {self.numero} fecha={self.fecha}>'

    def to_dict(self, include_lineas=False):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'numero': self.numero,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'es_apertura': self.es_apertura,
            'leyenda_global': self.leyenda_global,
            'estado': self.estado.value if self.estado else None,
            'total_debe': float(self.total_debe),
            'total_haber': float(self.total_haber),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_lineas:
            data['lineas'] = [linea.to_dict() for linea in self.lineas]
        return data


class AsientoLinea(db.Model):
    """Model for journal entry detail line."""

    __tablename__ = 'asiento_linea'

    id = db.Column(db.Integer, primary_key=True)
    asiento_id = db.Column(
        db.Integer,
        db.ForeignKey('asiento.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    item = db.Column(db.SmallInteger, nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    debe = db.Column(db.Numeric(15, 2), default=0)
    haber = db.Column(db.Numeric(15, 2), default=0)
    leyenda = db.Column(db.String(50))

    @property
    def importe(self):
        """Get the non-zero amount."""
        return float(self.debe) if self.debe else float(self.haber)

    @property
    def tipo_movimiento(self):
        """Get movement type (D for debit, H for credit)."""
        return 'D' if self.debe and self.debe > 0 else 'H'

    def __repr__(self):
        return f'<AsientoLinea {self.item}: {self.cuenta_id} D={self.debe} H={self.haber}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'asiento_id': self.asiento_id,
            'item': self.item,
            'cuenta_id': self.cuenta_id,
            'cuenta_codigo': self.cuenta.cuenta if self.cuenta else None,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'debe': float(self.debe) if self.debe else 0,
            'haber': float(self.haber) if self.haber else 0,
            'leyenda': self.leyenda
        }

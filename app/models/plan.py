"""Plan de Cuentas model."""
from datetime import datetime
from app.extensions import db


class Plan(db.Model):
    """Model for chart of accounts (Plan de Cuentas)."""

    __tablename__ = 'plan'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    cuenta = db.Column(db.String(10), nullable=False, index=True)
    nombre = db.Column(db.String(60), nullable=False)
    nivel = db.Column(db.SmallInteger, nullable=False)  # 1-9
    imputable = db.Column(db.String(1), default='N')  # S/N - Si es cuenta de detalle
    monetaria = db.Column(db.String(1), default='N')  # S/N - Si es cuenta monetaria
    ajustable = db.Column(db.String(1), default='N')  # S/N - Si se ajusta por inflacion
    tipo_saldo = db.Column(db.String(1), default='D')  # D=Deudor, A=Acreedor
    ultimo_saldo = db.Column(db.Numeric(15, 2), default=0)
    ultimo_movimiento = db.Column(db.Date)
    inflacion_acumulada = db.Column(db.Numeric(15, 2), default=0)
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint for empresa + cuenta
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'cuenta', name='uk_empresa_cuenta'),
    )

    # Relationships
    lineas_asiento = db.relationship('AsientoLinea', backref='cuenta', lazy='dynamic')
    saldos = db.relationship('Saldo', backref='cuenta', lazy='dynamic')

    @property
    def es_imputable(self):
        """Check if account is imputable (can receive entries)."""
        return self.imputable == 'S'

    @property
    def es_monetaria(self):
        """Check if account is monetary."""
        return self.monetaria == 'S'

    @property
    def es_ajustable(self):
        """Check if account is adjustable for inflation."""
        return self.ajustable == 'S'

    @property
    def es_deudora(self):
        """Check if account has debit nature."""
        return self.tipo_saldo == 'D'

    @property
    def cuenta_padre(self):
        """Get parent account code based on level."""
        if self.nivel <= 1:
            return None
        # Parent is one level up, typically removing last digit(s)
        return self.cuenta[:-1] if len(self.cuenta) > 1 else None

    def __repr__(self):
        return f'<Plan {self.cuenta}: {self.nombre}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'cuenta': self.cuenta,
            'nombre': self.nombre,
            'nivel': self.nivel,
            'imputable': self.imputable,
            'monetaria': self.monetaria,
            'ajustable': self.ajustable,
            'tipo_saldo': self.tipo_saldo,
            'ultimo_saldo': float(self.ultimo_saldo) if self.ultimo_saldo else 0,
            'ultimo_movimiento': self.ultimo_movimiento.isoformat() if self.ultimo_movimiento else None,
            'activa': self.activa
        }

    @staticmethod
    def get_by_cuenta(empresa_id, cuenta):
        """Get account by code."""
        return Plan.query.filter_by(empresa_id=empresa_id, cuenta=cuenta).first()

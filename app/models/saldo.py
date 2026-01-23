"""Saldo (Balance) model."""
from app.extensions import db


class Saldo(db.Model):
    """Model for account balance by period."""

    __tablename__ = 'saldo'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False, index=True)
    anio = db.Column(db.SmallInteger, nullable=False, index=True)
    mes = db.Column(db.SmallInteger, nullable=False)  # 1-12
    saldo = db.Column(db.Numeric(15, 2), default=0)
    debe_acumulado = db.Column(db.Numeric(15, 2), default=0)
    haber_acumulado = db.Column(db.Numeric(15, 2), default=0)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'cuenta_id', 'anio', 'mes', name='uk_cuenta_periodo'),
    )

    @property
    def periodo(self):
        """Get period as YYYY-MM string."""
        return f'{self.anio}-{self.mes:02d}'

    def __repr__(self):
        return f'<Saldo cuenta={self.cuenta_id} periodo={self.periodo} saldo={self.saldo}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'cuenta_id': self.cuenta_id,
            'cuenta_codigo': self.cuenta.cuenta if self.cuenta else None,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'anio': self.anio,
            'mes': self.mes,
            'periodo': self.periodo,
            'saldo': float(self.saldo) if self.saldo else 0,
            'debe_acumulado': float(self.debe_acumulado) if self.debe_acumulado else 0,
            'haber_acumulado': float(self.haber_acumulado) if self.haber_acumulado else 0
        }

    @staticmethod
    def get_or_create(empresa_id, cuenta_id, anio, mes):
        """Get existing balance or create new one."""
        saldo = Saldo.query.filter_by(
            empresa_id=empresa_id,
            cuenta_id=cuenta_id,
            anio=anio,
            mes=mes
        ).first()

        if not saldo:
            saldo = Saldo(
                empresa_id=empresa_id,
                cuenta_id=cuenta_id,
                anio=anio,
                mes=mes,
                saldo=0,
                debe_acumulado=0,
                haber_acumulado=0
            )
            db.session.add(saldo)

        return saldo

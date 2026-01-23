"""Saldo (Balance) Service."""
from decimal import Decimal
from app.extensions import db
from app.models import Plan, Saldo


class SaldoService:
    """Service for managing account balances."""

    @staticmethod
    def actualizar_saldo(cuenta_id, fecha, debe, haber, empresa_id):
        """Update balance for an account after a journal entry line.

        Args:
            cuenta_id: Account ID
            fecha: Entry date
            debe: Debit amount
            haber: Credit amount
            empresa_id: Company ID
        """
        anio = fecha.year
        mes = fecha.month

        # Get or create period balance
        saldo = Saldo.get_or_create(empresa_id, cuenta_id, anio, mes)

        # Convert to Decimal for precision
        debe = Decimal(str(debe)) if debe else Decimal('0')
        haber = Decimal(str(haber)) if haber else Decimal('0')

        # Update accumulated values
        saldo.debe_acumulado = (saldo.debe_acumulado or Decimal('0')) + debe
        saldo.haber_acumulado = (saldo.haber_acumulado or Decimal('0')) + haber

        # Update net balance (debit - credit)
        saldo.saldo = (saldo.saldo or Decimal('0')) + debe - haber

        # Update account's last balance and movement date
        cuenta = Plan.query.get(cuenta_id)
        if cuenta:
            cuenta.ultimo_saldo = (cuenta.ultimo_saldo or Decimal('0')) + debe - haber
            if not cuenta.ultimo_movimiento or fecha > cuenta.ultimo_movimiento:
                cuenta.ultimo_movimiento = fecha

    @staticmethod
    def revertir_saldo(cuenta_id, fecha, debe, haber, empresa_id):
        """Revert balance changes when voiding a journal entry.

        Args:
            cuenta_id: Account ID
            fecha: Entry date
            debe: Debit amount to revert
            haber: Credit amount to revert
            empresa_id: Company ID
        """
        anio = fecha.year
        mes = fecha.month

        saldo = Saldo.query.filter_by(
            empresa_id=empresa_id,
            cuenta_id=cuenta_id,
            anio=anio,
            mes=mes
        ).first()

        if saldo:
            # Convert to Decimal for precision
            debe = Decimal(str(debe)) if debe else Decimal('0')
            haber = Decimal(str(haber)) if haber else Decimal('0')

            # Revert accumulated values
            saldo.debe_acumulado = (saldo.debe_acumulado or Decimal('0')) - debe
            saldo.haber_acumulado = (saldo.haber_acumulado or Decimal('0')) - haber

            # Revert net balance
            saldo.saldo = (saldo.saldo or Decimal('0')) - debe + haber

        # Update account's last balance
        cuenta = Plan.query.get(cuenta_id)
        if cuenta:
            cuenta.ultimo_saldo = (cuenta.ultimo_saldo or Decimal('0')) - debe + haber

    @staticmethod
    def recalcular_saldos(empresa_id, cuenta_id=None):
        """Recalculate all balances from journal entries.

        Args:
            empresa_id: Company ID
            cuenta_id: Optional account ID to recalculate only one account
        """
        from app.models import Asiento, AsientoLinea, EstadoAsiento

        # Clear existing balances
        query = Saldo.query.filter_by(empresa_id=empresa_id)
        if cuenta_id:
            query = query.filter_by(cuenta_id=cuenta_id)
        query.delete()

        # Reset account balances
        plan_query = Plan.query.filter_by(empresa_id=empresa_id)
        if cuenta_id:
            plan_query = plan_query.filter_by(id=cuenta_id)
        plan_query.update({'ultimo_saldo': 0, 'ultimo_movimiento': None})

        # Process all active entries
        entries = (
            db.session.query(AsientoLinea, Asiento)
            .join(Asiento)
            .filter(
                Asiento.empresa_id == empresa_id,
                Asiento.estado == EstadoAsiento.ACTIVO
            )
        )

        if cuenta_id:
            entries = entries.filter(AsientoLinea.cuenta_id == cuenta_id)

        entries = entries.order_by(Asiento.fecha, Asiento.numero)

        for linea, asiento in entries.all():
            SaldoService.actualizar_saldo(
                linea.cuenta_id,
                asiento.fecha,
                linea.debe or 0,
                linea.haber or 0,
                empresa_id
            )

        db.session.commit()

    @staticmethod
    def get_saldo_cuenta(empresa_id, cuenta_id, anio, mes):
        """Get balance for a specific account and period.

        Args:
            empresa_id: Company ID
            cuenta_id: Account ID
            anio: Year
            mes: Month

        Returns:
            Saldo object or None
        """
        return Saldo.query.filter_by(
            empresa_id=empresa_id,
            cuenta_id=cuenta_id,
            anio=anio,
            mes=mes
        ).first()

    @staticmethod
    def get_saldo_acumulado(empresa_id, cuenta_id, hasta_anio, hasta_mes):
        """Get accumulated balance up to a specific period.

        Args:
            empresa_id: Company ID
            cuenta_id: Account ID
            hasta_anio: Year
            hasta_mes: Month

        Returns:
            Total accumulated balance
        """
        saldos = Saldo.query.filter(
            Saldo.empresa_id == empresa_id,
            Saldo.cuenta_id == cuenta_id,
            db.or_(
                Saldo.anio < hasta_anio,
                db.and_(Saldo.anio == hasta_anio, Saldo.mes <= hasta_mes)
            )
        ).all()

        return sum(s.saldo or 0 for s in saldos)

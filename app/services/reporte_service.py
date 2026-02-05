"""Reporte (Report) Service."""
from decimal import Decimal
from datetime import date
from sqlalchemy import func
from app.extensions import db
from app.models import Asiento, AsientoLinea, Plan, Saldo, EstadoAsiento


class ReporteService:
    """Service for generating accounting reports."""

    @staticmethod
    def libro_diario(empresa_id, fecha_desde, fecha_hasta):
        """Generate journal book report.

        Args:
            empresa_id: Company ID
            fecha_desde: Start date
            fecha_hasta: End date

        Returns:
            List of entries with their lines
        """
        asientos = (
            Asiento.query
            .filter(
                Asiento.empresa_id == empresa_id,
                Asiento.fecha >= fecha_desde,
                Asiento.fecha <= fecha_hasta,
                Asiento.estado == EstadoAsiento.ACTIVO
            )
            .order_by(Asiento.fecha, Asiento.numero)
            .all()
        )

        resultado = []
        total_debe = Decimal('0')
        total_haber = Decimal('0')

        for asiento in asientos:
            lineas = []
            for linea in asiento.lineas.order_by(AsientoLinea.item):
                lineas.append({
                    'item': linea.item,
                    'cuenta': linea.cuenta.cuenta,
                    'nombre': linea.cuenta.nombre,
                    'debe': float(linea.debe or 0),
                    'haber': float(linea.haber or 0),
                    'leyenda': linea.leyenda
                })
                total_debe += linea.debe or Decimal('0')
                total_haber += linea.haber or Decimal('0')

            resultado.append({
                'numero': asiento.numero,
                'fecha': asiento.fecha,
                'leyenda_global': asiento.leyenda_global,
                'es_apertura': asiento.es_apertura,
                'lineas': lineas,
                'total_debe': float(asiento.total_debe),
                'total_haber': float(asiento.total_haber)
            })

        return {
            'asientos': resultado,
            'total_debe': float(total_debe),
            'total_haber': float(total_haber)
        }

    @staticmethod
    def libro_mayor(empresa_id, fecha_desde, fecha_hasta, cuenta_desde=None, cuenta_hasta=None):
        """Generate ledger book report.

        Args:
            empresa_id: Company ID
            fecha_desde: Start date
            fecha_hasta: End date
            cuenta_desde: Start account code (optional)
            cuenta_hasta: End account code (optional)

        Returns:
            List of accounts with their movements and balances
        """
        # Get accounts to include
        query = Plan.query.filter(
            Plan.empresa_id == empresa_id,
            Plan.imputable == 'S',
            Plan.activa == True
        )

        if cuenta_desde:
            query = query.filter(Plan.cuenta >= cuenta_desde)
        if cuenta_hasta:
            query = query.filter(Plan.cuenta <= cuenta_hasta)

        cuentas = query.order_by(Plan.cuenta).all()

        resultado = []

        for cuenta in cuentas:
            # Get movements for this account in the period
            movimientos = (
                db.session.query(AsientoLinea, Asiento)
                .join(Asiento)
                .filter(
                    AsientoLinea.cuenta_id == cuenta.id,
                    Asiento.fecha >= fecha_desde,
                    Asiento.fecha <= fecha_hasta,
                    Asiento.estado == EstadoAsiento.ACTIVO
                )
                .order_by(Asiento.fecha, Asiento.numero)
                .all()
            )

            if not movimientos:
                continue

            # Calculate opening balance (movements before fecha_desde)
            saldo_anterior = db.session.query(
                func.coalesce(func.sum(AsientoLinea.debe), 0) -
                func.coalesce(func.sum(AsientoLinea.haber), 0)
            ).join(Asiento).filter(
                AsientoLinea.cuenta_id == cuenta.id,
                Asiento.fecha < fecha_desde,
                Asiento.estado == EstadoAsiento.ACTIVO
            ).scalar() or Decimal('0')

            lineas = []
            saldo = float(saldo_anterior)
            total_debe = Decimal('0')
            total_haber = Decimal('0')

            for linea, asiento in movimientos:
                debe = float(linea.debe or 0)
                haber = float(linea.haber or 0)
                saldo += debe - haber
                total_debe += linea.debe or Decimal('0')
                total_haber += linea.haber or Decimal('0')

                lineas.append({
                    'fecha': asiento.fecha,
                    'asiento': asiento.numero,
                    'leyenda': linea.leyenda or asiento.leyenda_global or '',
                    'debe': debe,
                    'haber': haber,
                    'saldo': saldo
                })

            resultado.append({
                'cuenta': cuenta.cuenta,
                'nombre': cuenta.nombre,
                'tipo_saldo': cuenta.tipo_saldo,
                'saldo_anterior': float(saldo_anterior),
                'movimientos': lineas,
                'total_debe': float(total_debe),
                'total_haber': float(total_haber),
                'saldo_final': saldo
            })

        return resultado

    @staticmethod
    def sumas_saldos(empresa_id, fecha_desde, fecha_hasta, incluir_cuentas_sin_movimiento=False):
        """Generate trial balance report (Sumas y Saldos).

        Args:
            empresa_id: Company ID
            fecha_desde: Start date (None to include all from beginning)
            fecha_hasta: End date
            incluir_cuentas_sin_movimiento: Include accounts with zero balance

        Returns:
            List of accounts with debit/credit sums and balances
        """
        # Get all imputable accounts
        cuentas_query = Plan.query.filter(
            Plan.empresa_id == empresa_id,
            Plan.imputable == 'S',
            Plan.activa == True
        ).order_by(Plan.cuenta)

        resultado = []
        total_debe = Decimal('0')
        total_haber = Decimal('0')
        total_saldo_deudor = Decimal('0')
        total_saldo_acreedor = Decimal('0')

        for cuenta in cuentas_query.all():
            # Build query for movements
            query = db.session.query(
                func.coalesce(func.sum(AsientoLinea.debe), 0).label('total_debe'),
                func.coalesce(func.sum(AsientoLinea.haber), 0).label('total_haber')
            ).join(Asiento).filter(
                AsientoLinea.cuenta_id == cuenta.id,
                Asiento.fecha <= fecha_hasta,
                Asiento.estado == EstadoAsiento.ACTIVO
            )

            # Add fecha_desde filter if provided
            if fecha_desde:
                query = query.filter(Asiento.fecha >= fecha_desde)

            totales = query.first()

            debe = totales.total_debe or Decimal('0')
            haber = totales.total_haber or Decimal('0')
            diferencia = debe - haber

            # Skip if no movements and not requested
            if not incluir_cuentas_sin_movimiento and debe == 0 and haber == 0:
                continue

            # Determine debit or credit balance
            if diferencia >= 0:
                saldo_deudor = diferencia
                saldo_acreedor = Decimal('0')
            else:
                saldo_deudor = Decimal('0')
                saldo_acreedor = abs(diferencia)

            resultado.append({
                'cuenta': cuenta.cuenta,
                'nombre': cuenta.nombre,
                'debe': float(debe),
                'haber': float(haber),
                'saldo_deudor': float(saldo_deudor),
                'saldo_acreedor': float(saldo_acreedor)
            })

            total_debe += debe
            total_haber += haber
            total_saldo_deudor += saldo_deudor
            total_saldo_acreedor += saldo_acreedor

        return {
            'cuentas': resultado,
            'total_debe': float(total_debe),
            'total_haber': float(total_haber),
            'total_saldo_deudor': float(total_saldo_deudor),
            'total_saldo_acreedor': float(total_saldo_acreedor)
        }

    @staticmethod
    def balance_general(empresa_id, fecha_desde, fecha_hasta):
        """Generate general balance report with hierarchical structure.

        Args:
            empresa_id: Company ID
            fecha_desde: Start date (None to include all from beginning)
            fecha_hasta: End date

        Returns:
            Hierarchical structure of accounts with balances
        """
        # Get all accounts ordered by code
        cuentas = Plan.query.filter(
            Plan.empresa_id == empresa_id,
            Plan.activa == True
        ).order_by(Plan.cuenta).all()

        # Calculate balances for imputable accounts
        saldos = {}
        for cuenta in cuentas:
            if cuenta.imputable == 'S':
                query = db.session.query(
                    func.coalesce(func.sum(AsientoLinea.debe), 0).label('total_debe'),
                    func.coalesce(func.sum(AsientoLinea.haber), 0).label('total_haber')
                ).join(Asiento).filter(
                    AsientoLinea.cuenta_id == cuenta.id,
                    Asiento.fecha <= fecha_hasta,
                    Asiento.estado == EstadoAsiento.ACTIVO
                )

                if fecha_desde:
                    query = query.filter(Asiento.fecha >= fecha_desde)

                totales = query.first()

                saldo = (totales.total_debe or 0) - (totales.total_haber or 0)
                saldos[cuenta.cuenta] = float(saldo)

        # Build hierarchical structure
        def get_saldo_jerarquico(cuenta_code):
            """Get balance including all child accounts."""
            total = saldos.get(cuenta_code, 0)
            for cuenta in cuentas:
                if cuenta.cuenta.startswith(cuenta_code) and cuenta.cuenta != cuenta_code:
                    # Only add direct imputable children
                    if cuenta.imputable == 'S':
                        total += saldos.get(cuenta.cuenta, 0)
            return total

        # Build result
        resultado = []
        for cuenta in cuentas:
            # Calculate hierarchical balance for non-imputable accounts
            if cuenta.imputable == 'S':
                saldo = saldos.get(cuenta.cuenta, 0)
            else:
                # Sum all child account balances
                saldo = 0
                for c in cuentas:
                    if c.cuenta.startswith(cuenta.cuenta) and c.imputable == 'S':
                        saldo += saldos.get(c.cuenta, 0)

            # Skip accounts with zero balance (except level 1)
            if saldo == 0 and cuenta.nivel > 1:
                continue

            resultado.append({
                'cuenta': cuenta.cuenta,
                'nombre': cuenta.nombre,
                'nivel': cuenta.nivel,
                'imputable': cuenta.imputable == 'S',
                'tipo_saldo': cuenta.tipo_saldo,
                'saldo': saldo,
                'indent': (cuenta.nivel - 1) * 20
            })

        # Calculate totals by main category (Activo, Pasivo, Patrimonio, etc.)
        totales = {}
        for cuenta in cuentas:
            if cuenta.nivel == 1:
                saldo = 0
                for c in cuentas:
                    if c.cuenta.startswith(cuenta.cuenta) and c.imputable == 'S':
                        saldo += saldos.get(c.cuenta, 0)
                totales[cuenta.cuenta] = {
                    'nombre': cuenta.nombre,
                    'saldo': saldo
                }

        return {
            'cuentas': resultado,
            'totales': totales
        }

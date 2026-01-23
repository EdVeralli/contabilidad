"""Inflacion (Inflation Adjustment) Service."""
from decimal import Decimal
from datetime import date
from sqlalchemy import func
from app.extensions import db
from app.models import (
    TablaInflacion, Plan, Asiento, AsientoLinea,
    EstadoAsiento
)
from .asiento_service import AsientoService


class InflacionService:
    """Service for inflation adjustment calculations."""

    @staticmethod
    def get_indice(empresa_id, codigo_tabla, anio, mes):
        """Get inflation index for a specific period.

        Args:
            empresa_id: Company ID
            codigo_tabla: Inflation table code
            anio: Year
            mes: Month

        Returns:
            Inflation index value or None
        """
        tabla = TablaInflacion.query.filter_by(
            empresa_id=empresa_id,
            codigo=codigo_tabla,
            anio=anio
        ).first()

        if tabla:
            return tabla.get_indice(mes)
        return None

    @staticmethod
    def calcular_factor_ajuste(empresa_id, codigo_tabla, mes_origen, anio_origen,
                                mes_destino, anio_destino):
        """Calculate adjustment factor between two periods.

        Args:
            empresa_id: Company ID
            codigo_tabla: Inflation table code
            mes_origen: Origin month
            anio_origen: Origin year
            mes_destino: Destination month
            anio_destino: Destination year

        Returns:
            Adjustment factor (destino / origen) or None
        """
        indice_origen = InflacionService.get_indice(
            empresa_id, codigo_tabla, anio_origen, mes_origen
        )
        indice_destino = InflacionService.get_indice(
            empresa_id, codigo_tabla, anio_destino, mes_destino
        )

        if indice_origen and indice_destino and indice_origen > 0:
            return Decimal(str(indice_destino)) / Decimal(str(indice_origen))
        return None

    @staticmethod
    def calcular_ajuste_cuenta(empresa_id, cuenta_id, fecha_hasta, codigo_tabla='A'):
        """Calculate inflation adjustment for a single account.

        Args:
            empresa_id: Company ID
            cuenta_id: Account ID
            fecha_hasta: Cutoff date
            codigo_tabla: Inflation table code (default 'A')

        Returns:
            Dictionary with adjustment details
        """
        cuenta = Plan.query.get(cuenta_id)
        if not cuenta or cuenta.ajustable != 'S':
            return None

        # Get all movements for this account up to fecha_hasta
        movimientos = (
            db.session.query(
                AsientoLinea.debe,
                AsientoLinea.haber,
                Asiento.fecha
            )
            .join(Asiento)
            .filter(
                AsientoLinea.cuenta_id == cuenta_id,
                Asiento.fecha <= fecha_hasta,
                Asiento.estado == EstadoAsiento.ACTIVO
            )
            .order_by(Asiento.fecha)
            .all()
        )

        if not movimientos:
            return None

        ajuste_total = Decimal('0')
        detalle = []
        mes_destino = fecha_hasta.month
        anio_destino = fecha_hasta.year

        for mov in movimientos:
            importe = (mov.debe or Decimal('0')) - (mov.haber or Decimal('0'))
            if importe == 0:
                continue

            mes_origen = mov.fecha.month
            anio_origen = mov.fecha.year

            factor = InflacionService.calcular_factor_ajuste(
                empresa_id, codigo_tabla,
                mes_origen, anio_origen,
                mes_destino, anio_destino
            )

            if factor and factor != 1:
                importe_ajustado = importe * factor
                ajuste = importe_ajustado - importe
                ajuste_total += ajuste

                detalle.append({
                    'fecha': mov.fecha,
                    'importe_original': float(importe),
                    'factor': float(factor),
                    'importe_ajustado': float(importe_ajustado),
                    'ajuste': float(ajuste)
                })

        return {
            'cuenta': cuenta.cuenta,
            'nombre': cuenta.nombre,
            'saldo_original': float(sum(
                (m.debe or 0) - (m.haber or 0) for m in movimientos
            )),
            'ajuste_total': float(ajuste_total),
            'saldo_ajustado': float(sum(
                (m.debe or 0) - (m.haber or 0) for m in movimientos
            ) + ajuste_total),
            'detalle': detalle
        }

    @staticmethod
    def calcular_ajuste_general(empresa_id, fecha_hasta, codigo_tabla='A'):
        """Calculate inflation adjustment for all adjustable accounts.

        Args:
            empresa_id: Company ID
            fecha_hasta: Cutoff date
            codigo_tabla: Inflation table code

        Returns:
            Dictionary with adjustment summary and details
        """
        # Get all adjustable accounts
        cuentas = Plan.query.filter(
            Plan.empresa_id == empresa_id,
            Plan.ajustable == 'S',
            Plan.imputable == 'S',
            Plan.activa == True
        ).order_by(Plan.cuenta).all()

        resultados = []
        total_ajuste_deudor = Decimal('0')
        total_ajuste_acreedor = Decimal('0')

        for cuenta in cuentas:
            resultado = InflacionService.calcular_ajuste_cuenta(
                empresa_id, cuenta.id, fecha_hasta, codigo_tabla
            )
            if resultado and abs(resultado['ajuste_total']) > 0.01:
                resultados.append(resultado)
                if resultado['ajuste_total'] > 0:
                    total_ajuste_deudor += Decimal(str(resultado['ajuste_total']))
                else:
                    total_ajuste_acreedor += abs(Decimal(str(resultado['ajuste_total'])))

        # REI (Resultado por Exposicion a la Inflacion)
        rei = total_ajuste_deudor - total_ajuste_acreedor

        return {
            'cuentas': resultados,
            'total_ajuste_deudor': float(total_ajuste_deudor),
            'total_ajuste_acreedor': float(total_ajuste_acreedor),
            'rei': float(rei),
            'fecha_hasta': fecha_hasta
        }

    @staticmethod
    def generar_asiento_ajuste(empresa_id, fecha, ajustes, cuenta_rei_id, usuario_id=None):
        """Generate inflation adjustment journal entry.

        Args:
            empresa_id: Company ID
            fecha: Entry date
            ajustes: List of adjustments from calcular_ajuste_general
            cuenta_rei_id: REI (inflation exposure result) account ID
            usuario_id: User ID

        Returns:
            Created Asiento object
        """
        lineas = []

        # Add adjustment lines for each account
        for ajuste in ajustes['cuentas']:
            cuenta = Plan.query.filter_by(
                empresa_id=empresa_id,
                cuenta=ajuste['cuenta']
            ).first()

            if cuenta and abs(ajuste['ajuste_total']) > 0.01:
                if ajuste['ajuste_total'] > 0:
                    lineas.append({
                        'cuenta_id': cuenta.id,
                        'debe': abs(ajuste['ajuste_total']),
                        'haber': 0,
                        'leyenda': 'Ajuste por inflacion'
                    })
                else:
                    lineas.append({
                        'cuenta_id': cuenta.id,
                        'debe': 0,
                        'haber': abs(ajuste['ajuste_total']),
                        'leyenda': 'Ajuste por inflacion'
                    })

        # Add REI counterpart line
        if ajustes['rei'] != 0:
            if ajustes['rei'] > 0:
                # REI is a credit (gain from inflation)
                lineas.append({
                    'cuenta_id': cuenta_rei_id,
                    'debe': 0,
                    'haber': abs(ajustes['rei']),
                    'leyenda': 'REI - Resultado Exposicion Inflacion'
                })
            else:
                # REI is a debit (loss from inflation)
                lineas.append({
                    'cuenta_id': cuenta_rei_id,
                    'debe': abs(ajustes['rei']),
                    'haber': 0,
                    'leyenda': 'REI - Resultado Exposicion Inflacion'
                })

        if lineas:
            return AsientoService.crear_asiento(
                empresa_id=empresa_id,
                fecha=fecha,
                lineas=lineas,
                leyenda_global=f'Asiento de Ajuste por Inflacion al {fecha.strftime("%d/%m/%Y")}',
                es_apertura=False,
                usuario_id=usuario_id
            )

        return None

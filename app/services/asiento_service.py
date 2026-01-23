"""Asiento (Journal Entry) Service."""
from decimal import Decimal
from datetime import date
from app.extensions import db
from app.models import Asiento, AsientoLinea, Plan, Ejercicio, EstadoAsiento
from .saldo_service import SaldoService


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class AsientoService:
    """Service for managing journal entries."""

    @staticmethod
    def validar_asiento(lineas, empresa_id, fecha=None, asiento_id=None):
        """Validate journal entry before saving.

        Args:
            lineas: List of entry lines (dict with cuenta_id, debe, haber, leyenda)
            empresa_id: Company ID
            fecha: Entry date (optional, for fiscal year validation)
            asiento_id: Existing entry ID if editing

        Raises:
            ValidationError: If validation fails
        """
        if not lineas:
            raise ValidationError('El asiento debe tener al menos una linea.')

        total_debe = Decimal('0')
        total_haber = Decimal('0')

        for i, linea in enumerate(lineas, 1):
            cuenta_id = linea.get('cuenta_id')
            debe = Decimal(str(linea.get('debe', 0) or 0))
            haber = Decimal(str(linea.get('haber', 0) or 0))

            # Validate account exists
            if not cuenta_id:
                raise ValidationError(f'Linea {i}: Debe seleccionar una cuenta.')

            cuenta = Plan.query.filter_by(id=cuenta_id, empresa_id=empresa_id).first()
            if not cuenta:
                raise ValidationError(f'Linea {i}: La cuenta no existe.')

            # Validate account is imputable
            if cuenta.imputable != 'S':
                raise ValidationError(
                    f'Linea {i}: La cuenta {cuenta.cuenta} no es imputable.'
                )

            # Validate account is active
            if not cuenta.activa:
                raise ValidationError(
                    f'Linea {i}: La cuenta {cuenta.cuenta} esta inactiva.'
                )

            # Validate amounts
            if debe < 0 or haber < 0:
                raise ValidationError(
                    f'Linea {i}: Los importes no pueden ser negativos.'
                )

            if debe == 0 and haber == 0:
                raise ValidationError(
                    f'Linea {i}: Debe ingresar un importe en Debe o Haber.'
                )

            if debe > 0 and haber > 0:
                raise ValidationError(
                    f'Linea {i}: Solo puede ingresar Debe o Haber, no ambos.'
                )

            total_debe += debe
            total_haber += haber

        # Validate balance
        if abs(total_debe - total_haber) > Decimal('0.01'):
            raise ValidationError(
                f'El asiento no esta balanceado. '
                f'Debe: {total_debe:,.2f}, Haber: {total_haber:,.2f}, '
                f'Diferencia: {abs(total_debe - total_haber):,.2f}'
            )

        if total_debe == 0:
            raise ValidationError('El asiento no tiene movimientos.')

        # Validate fiscal year if date provided
        if fecha:
            ejercicio = Ejercicio.query.filter(
                Ejercicio.empresa_id == empresa_id,
                Ejercicio.fecha_inicio <= fecha,
                Ejercicio.fecha_fin >= fecha
            ).first()

            if ejercicio and ejercicio.cerrado:
                raise ValidationError(
                    f'El ejercicio {ejercicio.anio} esta cerrado.'
                )

        return True

    @staticmethod
    def get_siguiente_numero(empresa_id):
        """Get next available entry number for the company.

        Args:
            empresa_id: Company ID

        Returns:
            Next entry number
        """
        ultimo = db.session.query(db.func.max(Asiento.numero)).filter(
            Asiento.empresa_id == empresa_id
        ).scalar()

        return (ultimo or 0) + 1

    @staticmethod
    def crear_asiento(empresa_id, fecha, lineas, leyenda_global=None,
                      es_apertura=False, usuario_id=None):
        """Create a new journal entry.

        Args:
            empresa_id: Company ID
            fecha: Entry date
            lineas: List of entry lines
            leyenda_global: Global description
            es_apertura: Whether this is an opening entry
            usuario_id: User ID creating the entry

        Returns:
            Created Asiento object

        Raises:
            ValidationError: If validation fails
        """
        # Validate
        AsientoService.validar_asiento(lineas, empresa_id, fecha)

        # Create header
        asiento = Asiento(
            empresa_id=empresa_id,
            numero=AsientoService.get_siguiente_numero(empresa_id),
            fecha=fecha,
            leyenda_global=leyenda_global,
            es_apertura=es_apertura,
            usuario_id=usuario_id
        )
        db.session.add(asiento)
        db.session.flush()

        # Create lines and update balances
        for i, linea_data in enumerate(lineas, 1):
            linea = AsientoLinea(
                asiento_id=asiento.id,
                item=i,
                cuenta_id=linea_data['cuenta_id'],
                debe=Decimal(str(linea_data.get('debe', 0) or 0)),
                haber=Decimal(str(linea_data.get('haber', 0) or 0)),
                leyenda=linea_data.get('leyenda', '')
            )
            db.session.add(linea)

            # Update balance
            SaldoService.actualizar_saldo(
                linea.cuenta_id,
                fecha,
                linea.debe,
                linea.haber,
                empresa_id
            )

        db.session.commit()
        return asiento

    @staticmethod
    def modificar_asiento(asiento_id, fecha, lineas, leyenda_global=None,
                          usuario_id=None):
        """Modify an existing journal entry.

        Args:
            asiento_id: Entry ID to modify
            fecha: New entry date
            lineas: New entry lines
            leyenda_global: Global description
            usuario_id: User ID modifying

        Returns:
            Modified Asiento object

        Raises:
            ValidationError: If validation fails
        """
        asiento = Asiento.query.get_or_404(asiento_id)

        if asiento.estado != EstadoAsiento.ACTIVO:
            raise ValidationError('No se puede modificar un asiento anulado.')

        # Validate new data
        AsientoService.validar_asiento(lineas, asiento.empresa_id, fecha)

        # Revert old balances
        for linea in asiento.lineas:
            SaldoService.revertir_saldo(
                linea.cuenta_id,
                asiento.fecha,
                linea.debe or 0,
                linea.haber or 0,
                asiento.empresa_id
            )

        # Delete old lines
        AsientoLinea.query.filter_by(asiento_id=asiento.id).delete()

        # Update header
        asiento.fecha = fecha
        asiento.leyenda_global = leyenda_global

        # Create new lines and update balances
        for i, linea_data in enumerate(lineas, 1):
            linea = AsientoLinea(
                asiento_id=asiento.id,
                item=i,
                cuenta_id=linea_data['cuenta_id'],
                debe=Decimal(str(linea_data.get('debe', 0) or 0)),
                haber=Decimal(str(linea_data.get('haber', 0) or 0)),
                leyenda=linea_data.get('leyenda', '')
            )
            db.session.add(linea)

            SaldoService.actualizar_saldo(
                linea.cuenta_id,
                fecha,
                linea.debe,
                linea.haber,
                asiento.empresa_id
            )

        db.session.commit()
        return asiento

    @staticmethod
    def anular_asiento(asiento_id, usuario_id):
        """Void a journal entry.

        Args:
            asiento_id: Entry ID to void
            usuario_id: User ID voiding the entry

        Returns:
            Voided Asiento object

        Raises:
            ValidationError: If already voided
        """
        asiento = Asiento.query.get_or_404(asiento_id)

        if asiento.estado == EstadoAsiento.ANULADO:
            raise ValidationError('El asiento ya esta anulado.')

        # Check fiscal year
        ejercicio = Ejercicio.query.filter(
            Ejercicio.empresa_id == asiento.empresa_id,
            Ejercicio.fecha_inicio <= asiento.fecha,
            Ejercicio.fecha_fin >= asiento.fecha
        ).first()

        if ejercicio and ejercicio.cerrado:
            raise ValidationError(
                f'No se puede anular. El ejercicio {ejercicio.anio} esta cerrado.'
            )

        # Revert balances
        for linea in asiento.lineas:
            SaldoService.revertir_saldo(
                linea.cuenta_id,
                asiento.fecha,
                linea.debe or 0,
                linea.haber or 0,
                asiento.empresa_id
            )

        # Mark as voided
        asiento.anular(usuario_id)
        db.session.commit()

        return asiento

    @staticmethod
    def get_asientos_periodo(empresa_id, fecha_desde, fecha_hasta,
                             solo_activos=True, page=1, per_page=50):
        """Get journal entries for a period.

        Args:
            empresa_id: Company ID
            fecha_desde: Start date
            fecha_hasta: End date
            solo_activos: Only active entries
            page: Page number
            per_page: Items per page

        Returns:
            Pagination object
        """
        query = Asiento.query.filter(
            Asiento.empresa_id == empresa_id,
            Asiento.fecha >= fecha_desde,
            Asiento.fecha <= fecha_hasta
        )

        if solo_activos:
            query = query.filter(Asiento.estado == EstadoAsiento.ACTIVO)

        return query.order_by(Asiento.fecha, Asiento.numero).paginate(
            page=page, per_page=per_page, error_out=False
        )

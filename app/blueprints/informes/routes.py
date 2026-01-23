"""Informes routes."""
from datetime import date
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from app.services.reporte_service import ReporteService
from . import informes_bp


def get_empresa_id():
    """Get current empresa_id from session."""
    return session.get('empresa_id')


@informes_bp.route('/libro-diario', methods=['GET', 'POST'])
@login_required
def libro_diario():
    """Libro Diario (Journal Book) report."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    # Default to current month
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    if fecha_desde:
        fecha_desde = date.fromisoformat(fecha_desde)
    else:
        fecha_desde = date.today().replace(day=1)

    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = date.today()

    # Generate report
    reporte = ReporteService.libro_diario(empresa_id, fecha_desde, fecha_hasta)

    return render_template(
        'informes/libro_diario.html',
        reporte=reporte,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


@informes_bp.route('/libro-mayor', methods=['GET', 'POST'])
@login_required
def libro_mayor():
    """Libro Mayor (Ledger Book) report."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    # Get parameters
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    cuenta_desde = request.args.get('cuenta_desde', '')
    cuenta_hasta = request.args.get('cuenta_hasta', '')

    if fecha_desde:
        fecha_desde = date.fromisoformat(fecha_desde)
    else:
        fecha_desde = date.today().replace(day=1)

    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = date.today()

    # Generate report
    reporte = ReporteService.libro_mayor(
        empresa_id, fecha_desde, fecha_hasta,
        cuenta_desde if cuenta_desde else None,
        cuenta_hasta if cuenta_hasta else None
    )

    return render_template(
        'informes/libro_mayor.html',
        reporte=reporte,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta_desde=cuenta_desde,
        cuenta_hasta=cuenta_hasta
    )


@informes_bp.route('/sumas-saldos', methods=['GET', 'POST'])
@login_required
def sumas_saldos():
    """Sumas y Saldos (Trial Balance) report."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    # Get parameters
    fecha_hasta = request.args.get('fecha_hasta')
    incluir_sin_mov = request.args.get('incluir_sin_mov', 'false') == 'true'

    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = date.today()

    # Generate report
    reporte = ReporteService.sumas_saldos(empresa_id, fecha_hasta, incluir_sin_mov)

    return render_template(
        'informes/sumas_saldos.html',
        reporte=reporte,
        fecha_hasta=fecha_hasta,
        incluir_sin_mov=incluir_sin_mov
    )


@informes_bp.route('/balance-general', methods=['GET', 'POST'])
@login_required
def balance_general():
    """Balance General (General Balance) report."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    # Get parameters
    fecha_hasta = request.args.get('fecha_hasta')

    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = date.today()

    # Generate report
    reporte = ReporteService.balance_general(empresa_id, fecha_hasta)

    return render_template(
        'informes/balance_general.html',
        reporte=reporte,
        fecha_hasta=fecha_hasta
    )

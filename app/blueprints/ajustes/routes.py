"""Ajustes routes."""
from datetime import date
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import TablaInflacion, Plan
from app.services.inflacion_service import InflacionService
from app.services.asiento_service import ValidationError
from . import ajustes_bp


def get_empresa_id():
    """Get current empresa_id from session."""
    return session.get('empresa_id')


@ajustes_bp.route('/indices')
@login_required
def indices():
    """List inflation index tables."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    anio = request.args.get('anio', date.today().year, type=int)

    tablas = TablaInflacion.query.filter_by(
        empresa_id=empresa_id,
        anio=anio
    ).order_by(TablaInflacion.codigo).all()

    # Get available years
    anios = db.session.query(TablaInflacion.anio).filter_by(
        empresa_id=empresa_id
    ).distinct().order_by(TablaInflacion.anio.desc()).all()
    anios = [a[0] for a in anios]

    if anio not in anios:
        anios.append(anio)
        anios.sort(reverse=True)

    return render_template(
        'ajustes/indices.html',
        tablas=tablas,
        anio=anio,
        anios=anios
    )


@ajustes_bp.route('/indices/edit', methods=['GET', 'POST'])
@login_required
def indices_edit():
    """Edit inflation indices."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    codigo = request.args.get('codigo', 'A')
    anio = request.args.get('anio', date.today().year, type=int)

    tabla = TablaInflacion.query.filter_by(
        empresa_id=empresa_id,
        codigo=codigo,
        anio=anio
    ).first()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '')

        if not tabla:
            tabla = TablaInflacion(
                empresa_id=empresa_id,
                codigo=codigo,
                anio=anio,
                titulo=titulo
            )
            db.session.add(tabla)

        tabla.titulo = titulo

        # Update monthly indices
        for mes in range(1, 13):
            valor = request.form.get(f'indice_{mes:02d}', 0)
            try:
                tabla.set_indice(mes, float(valor) if valor else 0)
            except ValueError:
                pass

        db.session.commit()
        flash(f'Indices de {anio} actualizados correctamente.', 'success')
        return redirect(url_for('ajustes.indices', anio=anio))

    meses = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    indices_actuales = []
    if tabla:
        indices_actuales = [tabla.get_indice(m) for m in range(1, 13)]
    else:
        indices_actuales = [0] * 12

    return render_template(
        'ajustes/indices_edit.html',
        tabla=tabla,
        codigo=codigo,
        anio=anio,
        meses=meses,
        indices=indices_actuales
    )


@ajustes_bp.route('/ajustar', methods=['GET', 'POST'])
@login_required
def ajustar():
    """Calculate and generate inflation adjustment."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    fecha_hasta = request.args.get('fecha_hasta')
    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = date.today()

    codigo_tabla = request.args.get('tabla', 'A')

    # Calculate adjustment
    ajustes = InflacionService.calcular_ajuste_general(
        empresa_id, fecha_hasta, codigo_tabla
    )

    # Get REI account options
    cuentas_rei = Plan.query.filter(
        Plan.empresa_id == empresa_id,
        Plan.imputable == 'S',
        Plan.activa == True,
        Plan.cuenta.like('5%')  # Typically results accounts start with 5
    ).order_by(Plan.cuenta).all()

    return render_template(
        'ajustes/ajustar.html',
        ajustes=ajustes,
        fecha_hasta=fecha_hasta,
        codigo_tabla=codigo_tabla,
        cuentas_rei=cuentas_rei
    )


@ajustes_bp.route('/ajustar/generar', methods=['POST'])
@login_required
def generar_asiento_ajuste():
    """Generate inflation adjustment entry."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    fecha_hasta = request.form.get('fecha_hasta')
    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = date.today()

    codigo_tabla = request.form.get('codigo_tabla', 'A')
    cuenta_rei_id = request.form.get('cuenta_rei_id', type=int)

    if not cuenta_rei_id:
        flash('Debe seleccionar una cuenta REI.', 'danger')
        return redirect(url_for('ajustes.ajustar', fecha_hasta=fecha_hasta, tabla=codigo_tabla))

    try:
        # Recalculate adjustments
        ajustes = InflacionService.calcular_ajuste_general(
            empresa_id, fecha_hasta, codigo_tabla
        )

        if not ajustes['cuentas']:
            flash('No hay ajustes para generar.', 'warning')
            return redirect(url_for('ajustes.ajustar', fecha_hasta=fecha_hasta, tabla=codigo_tabla))

        # Generate entry
        asiento = InflacionService.generar_asiento_ajuste(
            empresa_id=empresa_id,
            fecha=fecha_hasta,
            ajustes=ajustes,
            cuenta_rei_id=cuenta_rei_id,
            usuario_id=current_user.id
        )

        if asiento:
            flash(f'Asiento de ajuste {asiento.numero} generado exitosamente.', 'success')
            return redirect(url_for('asientos.view', id=asiento.id))
        else:
            flash('No se genero ningun asiento.', 'warning')

    except ValidationError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al generar asiento: {str(e)}', 'danger')

    return redirect(url_for('ajustes.ajustar', fecha_hasta=fecha_hasta, tabla=codigo_tabla))

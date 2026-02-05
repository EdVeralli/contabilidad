"""Asientos routes."""
from datetime import date, datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Asiento, AsientoLinea, Plan, EstadoAsiento, Ejercicio
from app.services import AsientoService, SaldoService
from app.services.asiento_service import ValidationError
from . import asientos_bp
from .forms import AsientoForm, BusquedaAsientoForm


def get_empresa_id():
    """Get current empresa_id from session."""
    return session.get('empresa_id')


def get_ejercicios(empresa_id):
    """Get all ejercicios for empresa ordered by year desc."""
    return Ejercicio.query.filter_by(empresa_id=empresa_id).order_by(Ejercicio.anio.desc()).all()


@asientos_bp.route('/')
@login_required
def index():
    """List journal entries."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    # Get ejercicios for selector
    ejercicios = get_ejercicios(empresa_id)

    form = BusquedaAsientoForm(request.args)

    # Check if ejercicio was selected
    ejercicio_id = request.args.get('ejercicio_id', type=int)
    ejercicio_seleccionado = None
    if ejercicio_id:
        ejercicio_seleccionado = Ejercicio.query.get(ejercicio_id)
        if ejercicio_seleccionado:
            form.fecha_desde.data = ejercicio_seleccionado.fecha_inicio
            form.fecha_hasta.data = ejercicio_seleccionado.fecha_fin

    # Default date range: current month
    if not form.fecha_desde.data:
        form.fecha_desde.data = date.today().replace(day=1)
    if not form.fecha_hasta.data:
        form.fecha_hasta.data = date.today()

    query = Asiento.query.filter(
        Asiento.empresa_id == empresa_id,
        Asiento.fecha >= form.fecha_desde.data,
        Asiento.fecha <= form.fecha_hasta.data
    )

    # Apply filters
    if form.numero.data:
        query = query.filter(Asiento.numero == int(form.numero.data))

    if form.leyenda.data:
        search = f'%{form.leyenda.data}%'
        query = query.filter(Asiento.leyenda_global.ilike(search))

    if form.cuenta.data:
        # Search by account code
        cuenta = Plan.query.filter_by(
            empresa_id=empresa_id,
            cuenta=form.cuenta.data
        ).first()
        if cuenta:
            asiento_ids = db.session.query(AsientoLinea.asiento_id).filter(
                AsientoLinea.cuenta_id == cuenta.id
            ).distinct()
            query = query.filter(Asiento.id.in_(asiento_ids))

    page = request.args.get('page', 1, type=int)
    asientos = query.order_by(
        Asiento.fecha.desc(),
        Asiento.numero.desc()
    ).paginate(page=page, per_page=30, error_out=False)

    return render_template('asientos/index.html',
                          asientos=asientos,
                          form=form,
                          ejercicios=ejercicios,
                          ejercicio_seleccionado=ejercicio_seleccionado)


@asientos_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new journal entry."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    form = AsientoForm()

    if request.method == 'POST':
        # Get lines from JSON data
        lineas_json = request.form.get('lineas')
        if lineas_json:
            import json
            lineas = json.loads(lineas_json)

            try:
                asiento = AsientoService.crear_asiento(
                    empresa_id=empresa_id,
                    fecha=form.fecha.data,
                    lineas=lineas,
                    leyenda_global=form.leyenda_global.data,
                    es_apertura=form.es_apertura.data,
                    usuario_id=current_user.id
                )
                flash(f'Asiento {asiento.numero} creado exitosamente.', 'success')
                return redirect(url_for('asientos.view', id=asiento.id))

            except ValidationError as e:
                flash(str(e), 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al crear asiento: {str(e)}', 'danger')

    siguiente_numero = AsientoService.get_siguiente_numero(empresa_id)

    return render_template(
        'asientos/form.html',
        form=form,
        title='Nuevo Asiento',
        siguiente_numero=siguiente_numero
    )


@asientos_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit existing journal entry."""
    empresa_id = get_empresa_id()
    asiento = Asiento.query.filter_by(id=id, empresa_id=empresa_id).first_or_404()

    if asiento.estado == EstadoAsiento.ANULADO:
        flash('No se puede editar un asiento anulado.', 'warning')
        return redirect(url_for('asientos.view', id=id))

    form = AsientoForm(obj=asiento)

    if request.method == 'POST':
        lineas_json = request.form.get('lineas')
        if lineas_json:
            import json
            lineas = json.loads(lineas_json)

            try:
                AsientoService.modificar_asiento(
                    asiento_id=asiento.id,
                    fecha=form.fecha.data,
                    lineas=lineas,
                    leyenda_global=form.leyenda_global.data,
                    usuario_id=current_user.id
                )
                flash(f'Asiento {asiento.numero} actualizado exitosamente.', 'success')
                return redirect(url_for('asientos.view', id=asiento.id))

            except ValidationError as e:
                flash(str(e), 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al modificar asiento: {str(e)}', 'danger')

    # Prepare existing lines for template
    lineas_existentes = [{
        'cuenta_id': l.cuenta_id,
        'cuenta_codigo': l.cuenta.cuenta,
        'cuenta_nombre': l.cuenta.nombre,
        'debe': float(l.debe) if l.debe else 0,
        'haber': float(l.haber) if l.haber else 0,
        'leyenda': l.leyenda or ''
    } for l in asiento.lineas.order_by(AsientoLinea.item)]

    return render_template(
        'asientos/form.html',
        form=form,
        title=f'Editar Asiento {asiento.numero}',
        asiento=asiento,
        lineas_existentes=lineas_existentes
    )


@asientos_bp.route('/<int:id>/view')
@login_required
def view(id):
    """View journal entry details."""
    empresa_id = get_empresa_id()
    asiento = Asiento.query.filter_by(id=id, empresa_id=empresa_id).first_or_404()

    return render_template('asientos/view.html', asiento=asiento)


@asientos_bp.route('/<int:id>/anular', methods=['POST'])
@login_required
def anular(id):
    """Void a journal entry."""
    empresa_id = get_empresa_id()
    asiento = Asiento.query.filter_by(id=id, empresa_id=empresa_id).first_or_404()

    try:
        AsientoService.anular_asiento(asiento.id, current_user.id)
        flash(f'Asiento {asiento.numero} anulado exitosamente.', 'success')
    except ValidationError as e:
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al anular asiento: {str(e)}', 'danger')

    return redirect(url_for('asientos.view', id=id))


@asientos_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard stats."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        return jsonify({'error': 'No empresa selected'}), 400

    # Get stats
    total_cuentas = Plan.query.filter_by(empresa_id=empresa_id, activa=True).count()
    total_asientos = Asiento.query.filter_by(
        empresa_id=empresa_id,
        estado=EstadoAsiento.ACTIVO
    ).count()

    ultimo_asiento = Asiento.query.filter_by(
        empresa_id=empresa_id,
        estado=EstadoAsiento.ACTIVO
    ).order_by(Asiento.fecha.desc(), Asiento.numero.desc()).first()

    # Get last 5 entries
    ultimos = Asiento.query.filter_by(
        empresa_id=empresa_id,
        estado=EstadoAsiento.ACTIVO
    ).order_by(Asiento.fecha.desc(), Asiento.numero.desc()).limit(5).all()

    return jsonify({
        'total_cuentas': total_cuentas,
        'total_asientos': total_asientos,
        'ultimo_asiento': ultimo_asiento.fecha.strftime('%d/%m/%Y') if ultimo_asiento else '-',
        'ejercicio_actual': date.today().year,
        'ultimos_asientos': [{
            'numero': a.numero,
            'fecha': a.fecha.strftime('%d/%m/%Y'),
            'leyenda': a.leyenda_global[:30] if a.leyenda_global else '-',
            'total': float(a.total_debe)
        } for a in ultimos]
    })

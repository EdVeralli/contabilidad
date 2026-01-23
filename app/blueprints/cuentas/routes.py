"""Cuentas routes."""
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Plan, Asiento, AsientoLinea
from . import cuentas_bp
from .forms import CuentaForm, BusquedaCuentaForm


def get_empresa_id():
    """Get current empresa_id from session."""
    return session.get('empresa_id')


@cuentas_bp.route('/')
@login_required
def index():
    """List all accounts."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    form = BusquedaCuentaForm(request.args)
    query = Plan.query.filter_by(empresa_id=empresa_id)

    # Apply filters
    if form.q.data:
        search = f'%{form.q.data}%'
        query = query.filter(
            db.or_(
                Plan.cuenta.ilike(search),
                Plan.nombre.ilike(search)
            )
        )

    if form.nivel.data and form.nivel.data > 0:
        query = query.filter(Plan.nivel == form.nivel.data)

    if form.imputable.data:
        query = query.filter(Plan.imputable == form.imputable.data)

    if form.activa.data:
        query = query.filter(Plan.activa == (form.activa.data == '1'))

    cuentas = query.order_by(Plan.cuenta).all()

    return render_template('cuentas/index.html', cuentas=cuentas, form=form)


@cuentas_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new account."""
    empresa_id = get_empresa_id()
    if not empresa_id:
        flash('Debe seleccionar una empresa.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    form = CuentaForm(empresa_id=empresa_id)

    if form.validate_on_submit():
        cuenta = Plan(
            empresa_id=empresa_id,
            cuenta=form.cuenta.data.strip(),
            nombre=form.nombre.data.strip(),
            nivel=form.nivel.data,
            imputable=form.imputable.data,
            monetaria=form.monetaria.data,
            ajustable=form.ajustable.data,
            tipo_saldo=form.tipo_saldo.data,
            activa=form.activa.data
        )
        db.session.add(cuenta)
        db.session.commit()

        flash(f'Cuenta {cuenta.cuenta} creada exitosamente.', 'success')
        return redirect(url_for('cuentas.index'))

    return render_template('cuentas/form.html', form=form, title='Nueva Cuenta')


@cuentas_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit existing account."""
    empresa_id = get_empresa_id()
    cuenta = Plan.query.filter_by(id=id, empresa_id=empresa_id).first_or_404()

    form = CuentaForm(
        empresa_id=empresa_id,
        original_cuenta=cuenta.cuenta,
        obj=cuenta
    )

    if form.validate_on_submit():
        cuenta.cuenta = form.cuenta.data.strip()
        cuenta.nombre = form.nombre.data.strip()
        cuenta.nivel = form.nivel.data
        cuenta.imputable = form.imputable.data
        cuenta.monetaria = form.monetaria.data
        cuenta.ajustable = form.ajustable.data
        cuenta.tipo_saldo = form.tipo_saldo.data
        cuenta.activa = form.activa.data

        db.session.commit()
        flash(f'Cuenta {cuenta.cuenta} actualizada exitosamente.', 'success')
        return redirect(url_for('cuentas.index'))

    return render_template('cuentas/form.html', form=form, title='Editar Cuenta', cuenta=cuenta)


@cuentas_bp.route('/<int:id>/view')
@login_required
def view(id):
    """View account details."""
    empresa_id = get_empresa_id()
    cuenta = Plan.query.filter_by(id=id, empresa_id=empresa_id).first_or_404()

    # Get recent movements
    movimientos = (
        db.session.query(AsientoLinea, Asiento)
        .join(Asiento)
        .filter(AsientoLinea.cuenta_id == cuenta.id)
        .order_by(Asiento.fecha.desc(), Asiento.numero.desc())
        .limit(50)
        .all()
    )

    return render_template('cuentas/view.html', cuenta=cuenta, movimientos=movimientos)


@cuentas_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete account."""
    empresa_id = get_empresa_id()
    cuenta = Plan.query.filter_by(id=id, empresa_id=empresa_id).first_or_404()

    # Check if account has movements
    has_movements = AsientoLinea.query.filter_by(cuenta_id=cuenta.id).first()
    if has_movements:
        flash('No se puede eliminar la cuenta porque tiene movimientos asociados.', 'danger')
        return redirect(url_for('cuentas.index'))

    db.session.delete(cuenta)
    db.session.commit()
    flash(f'Cuenta {cuenta.cuenta} eliminada exitosamente.', 'success')
    return redirect(url_for('cuentas.index'))


@cuentas_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for account search (for autocomplete)."""
    empresa_id = get_empresa_id()
    q = request.args.get('q', '')
    imputable_only = request.args.get('imputable', 'false') == 'true'

    query = Plan.query.filter_by(empresa_id=empresa_id, activa=True)

    if q:
        search = f'%{q}%'
        query = query.filter(
            db.or_(
                Plan.cuenta.ilike(search),
                Plan.nombre.ilike(search)
            )
        )

    if imputable_only:
        query = query.filter(Plan.imputable == 'S')

    cuentas = query.order_by(Plan.cuenta).limit(20).all()

    return jsonify([{
        'id': c.id,
        'cuenta': c.cuenta,
        'nombre': c.nombre,
        'imputable': c.imputable,
        'tipo_saldo': c.tipo_saldo,
        'text': f'{c.cuenta} - {c.nombre}'
    } for c in cuentas])


@cuentas_bp.route('/api/get/<int:id>')
@login_required
def api_get(id):
    """API endpoint to get account details."""
    empresa_id = get_empresa_id()
    cuenta = Plan.query.filter_by(id=id, empresa_id=empresa_id).first()

    if not cuenta:
        return jsonify({'error': 'Cuenta no encontrada'}), 404

    return jsonify(cuenta.to_dict())


@cuentas_bp.route('/api/tree')
@login_required
def api_tree():
    """API endpoint for hierarchical account tree."""
    empresa_id = get_empresa_id()
    cuentas = Plan.query.filter_by(
        empresa_id=empresa_id,
        activa=True
    ).order_by(Plan.cuenta).all()

    # Build tree structure
    tree = []
    for cuenta in cuentas:
        tree.append({
            'id': cuenta.id,
            'cuenta': cuenta.cuenta,
            'nombre': cuenta.nombre,
            'nivel': cuenta.nivel,
            'imputable': cuenta.imputable == 'S',
            'saldo': float(cuenta.ultimo_saldo) if cuenta.ultimo_saldo else 0,
            'indent': '&nbsp;' * ((cuenta.nivel - 1) * 4)
        })

    return jsonify(tree)

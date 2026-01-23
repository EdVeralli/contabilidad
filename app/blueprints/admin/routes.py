"""Admin routes."""
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from functools import wraps
from datetime import date
from app.extensions import db
from app.models import Empresa, Usuario, Ejercicio
from . import admin_bp


def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/empresas')
@login_required
@admin_required
def empresas():
    """List all companies."""
    empresas = Empresa.query.order_by(Empresa.codigo).all()
    return render_template('admin/empresas.html', empresas=empresas)


@admin_bp.route('/empresas/create', methods=['GET', 'POST'])
@login_required
@admin_required
def empresa_create():
    """Create new company."""
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        nombre = request.form.get('nombre', '').strip()
        comentario = request.form.get('comentario', '').strip()

        if not codigo or not nombre:
            flash('Codigo y nombre son requeridos.', 'danger')
            return render_template('admin/empresa_form.html', title='Nueva Empresa')

        if Empresa.query.filter_by(codigo=codigo).first():
            flash('Ya existe una empresa con ese codigo.', 'danger')
            return render_template('admin/empresa_form.html', title='Nueva Empresa')

        empresa = Empresa(
            codigo=codigo,
            nombre=nombre,
            comentario=comentario,
            activa=True
        )
        db.session.add(empresa)
        db.session.commit()

        flash(f'Empresa {codigo} creada exitosamente.', 'success')
        return redirect(url_for('admin.empresas'))

    return render_template('admin/empresa_form.html', title='Nueva Empresa')


@admin_bp.route('/empresas/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def empresa_edit(id):
    """Edit company."""
    empresa = Empresa.query.get_or_404(id)

    if request.method == 'POST':
        empresa.codigo = request.form.get('codigo', '').strip().upper()
        empresa.nombre = request.form.get('nombre', '').strip()
        empresa.comentario = request.form.get('comentario', '').strip()
        empresa.activa = 'activa' in request.form

        db.session.commit()
        flash(f'Empresa {empresa.codigo} actualizada.', 'success')
        return redirect(url_for('admin.empresas'))

    return render_template('admin/empresa_form.html', title='Editar Empresa', empresa=empresa)


@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    """List all users."""
    usuarios = Usuario.query.order_by(Usuario.username).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin_bp.route('/usuarios/create', methods=['GET', 'POST'])
@login_required
@admin_required
def usuario_create():
    """Create new user."""
    empresas = Empresa.query.filter_by(activa=True).all()

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        empresa_id = request.form.get('empresa_id', type=int)
        is_admin = 'is_admin' in request.form

        if not username or not password:
            flash('Usuario y contraseña son requeridos.', 'danger')
            return render_template('admin/usuario_form.html', title='Nuevo Usuario', empresas=empresas)

        if Usuario.query.filter_by(username=username).first():
            flash('Ya existe un usuario con ese nombre.', 'danger')
            return render_template('admin/usuario_form.html', title='Nuevo Usuario', empresas=empresas)

        usuario = Usuario(
            username=username,
            nombre=nombre,
            email=email,
            empresa_id=empresa_id,
            is_admin=is_admin,
            activo=True
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        flash(f'Usuario {username} creado exitosamente.', 'success')
        return redirect(url_for('admin.usuarios'))

    return render_template('admin/usuario_form.html', title='Nuevo Usuario', empresas=empresas)


@admin_bp.route('/usuarios/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def usuario_edit(id):
    """Edit user."""
    usuario = Usuario.query.get_or_404(id)
    empresas = Empresa.query.filter_by(activa=True).all()

    if request.method == 'POST':
        usuario.nombre = request.form.get('nombre', '').strip()
        usuario.email = request.form.get('email', '').strip()
        usuario.empresa_id = request.form.get('empresa_id', type=int)
        usuario.is_admin = 'is_admin' in request.form
        usuario.activo = 'activo' in request.form

        new_password = request.form.get('password', '')
        if new_password:
            usuario.set_password(new_password)

        db.session.commit()
        flash(f'Usuario {usuario.username} actualizado.', 'success')
        return redirect(url_for('admin.usuarios'))

    return render_template('admin/usuario_form.html', title='Editar Usuario',
                          usuario=usuario, empresas=empresas)


# ==================== EJERCICIOS ====================

@admin_bp.route('/ejercicios')
@login_required
def ejercicios():
    """List all fiscal years for current empresa."""
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        flash('Debe seleccionar una empresa primero.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    empresa = Empresa.query.get(empresa_id)
    ejercicios = Ejercicio.query.filter_by(empresa_id=empresa_id).order_by(Ejercicio.anio.desc()).all()
    return render_template('admin/ejercicios.html', ejercicios=ejercicios, empresa=empresa)


@admin_bp.route('/ejercicios/create', methods=['GET', 'POST'])
@login_required
def ejercicio_create():
    """Create new fiscal year."""
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        flash('Debe seleccionar una empresa primero.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    empresa = Empresa.query.get(empresa_id)

    if request.method == 'POST':
        anio = request.form.get('anio', type=int)
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        if not anio or not fecha_inicio or not fecha_fin:
            flash('Todos los campos son requeridos.', 'danger')
            return render_template('admin/ejercicio_form.html', title='Nuevo Ejercicio', empresa=empresa)

        # Check if year already exists for this empresa
        if Ejercicio.query.filter_by(empresa_id=empresa_id, anio=anio).first():
            flash(f'Ya existe un ejercicio para el año {anio}.', 'danger')
            return render_template('admin/ejercicio_form.html', title='Nuevo Ejercicio', empresa=empresa)

        ejercicio = Ejercicio(
            empresa_id=empresa_id,
            anio=anio,
            fecha_inicio=date.fromisoformat(fecha_inicio),
            fecha_fin=date.fromisoformat(fecha_fin),
            cerrado=False
        )
        db.session.add(ejercicio)
        db.session.commit()

        flash(f'Ejercicio {anio} creado exitosamente.', 'success')
        return redirect(url_for('admin.ejercicios'))

    # Suggest next year
    ultimo_ejercicio = Ejercicio.query.filter_by(empresa_id=empresa_id).order_by(Ejercicio.anio.desc()).first()
    anio_sugerido = (ultimo_ejercicio.anio + 1) if ultimo_ejercicio else date.today().year

    return render_template('admin/ejercicio_form.html',
                          title='Nuevo Ejercicio',
                          empresa=empresa,
                          anio_sugerido=anio_sugerido)


@admin_bp.route('/ejercicios/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def ejercicio_edit(id):
    """Edit fiscal year."""
    ejercicio = Ejercicio.query.get_or_404(id)
    empresa = Empresa.query.get(ejercicio.empresa_id)

    # Verify it belongs to current empresa
    if ejercicio.empresa_id != session.get('empresa_id'):
        flash('No tiene permisos para editar este ejercicio.', 'danger')
        return redirect(url_for('admin.ejercicios'))

    if request.method == 'POST':
        ejercicio.anio = request.form.get('anio', type=int)
        ejercicio.fecha_inicio = date.fromisoformat(request.form.get('fecha_inicio'))
        ejercicio.fecha_fin = date.fromisoformat(request.form.get('fecha_fin'))
        ejercicio.cerrado = 'cerrado' in request.form

        db.session.commit()
        flash(f'Ejercicio {ejercicio.anio} actualizado.', 'success')
        return redirect(url_for('admin.ejercicios'))

    return render_template('admin/ejercicio_form.html',
                          title='Editar Ejercicio',
                          ejercicio=ejercicio,
                          empresa=empresa)


@admin_bp.route('/ejercicios/<int:id>/cerrar', methods=['POST'])
@login_required
def ejercicio_cerrar(id):
    """Close fiscal year."""
    ejercicio = Ejercicio.query.get_or_404(id)

    # Verify it belongs to current empresa
    if ejercicio.empresa_id != session.get('empresa_id'):
        flash('No tiene permisos para cerrar este ejercicio.', 'danger')
        return redirect(url_for('admin.ejercicios'))

    ejercicio.cerrado = True
    db.session.commit()

    flash(f'Ejercicio {ejercicio.anio} cerrado.', 'success')
    return redirect(url_for('admin.ejercicios'))

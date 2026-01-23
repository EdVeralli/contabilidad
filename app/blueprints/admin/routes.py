"""Admin routes."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import Empresa, Usuario
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

"""Authentication routes."""
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import Usuario, Empresa
from . import auth_bp
from .forms import LoginForm, ChangePasswordForm, SelectEmpresaForm


@auth_bp.route('/')
def index():
    """Root redirect to dashboard or login."""
    if current_user.is_authenticated:
        # Check if empresa is selected
        if not session.get('empresa_id'):
            return redirect(url_for('auth.select_empresa'))
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        if not session.get('empresa_id'):
            return redirect(url_for('auth.select_empresa'))
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.activo:
            flash('Su cuenta está desactivada. Contacte al administrador.', 'warning')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=form.remember_me.data)
        user.update_last_login()

        # Always redirect to empresa selection after login
        return redirect(url_for('auth.select_empresa'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    session.clear()
    flash('Ha cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard."""
    # Require empresa selection
    if not session.get('empresa_id'):
        flash('Debe seleccionar una empresa para continuar.', 'warning')
        return redirect(url_for('auth.select_empresa'))

    empresa = Empresa.query.get(session.get('empresa_id'))
    return render_template('auth/dashboard.html', empresa=empresa)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle password change."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('La contraseña actual es incorrecta.', 'danger')
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Su contraseña ha sido actualizada.', 'success')
        return redirect(url_for('auth.dashboard'))

    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/select-empresa', methods=['GET', 'POST'])
@login_required
def select_empresa():
    """Select company to work with - required for all users."""
    form = SelectEmpresaForm()
    empresas = Empresa.query.filter_by(activa=True).order_by(Empresa.codigo).all()
    form.empresa_id.choices = [(e.id, f'{e.codigo} - {e.nombre}') for e in empresas]

    if form.validate_on_submit():
        session['empresa_id'] = form.empresa_id.data
        empresa = Empresa.query.get(form.empresa_id.data)
        flash(f'Trabajando con: {empresa.nombre}', 'success')
        return redirect(url_for('auth.dashboard'))

    return render_template('auth/select_empresa.html', form=form, empresas=empresas)


def get_current_empresa_id():
    """Get current empresa_id from session."""
    return session.get('empresa_id')

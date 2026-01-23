"""Flask application factory."""
import os
from flask import Flask
from dotenv import load_dotenv

from .config import config
from .extensions import db, login_manager, migrate, csrf

# Get the base directory (vero_contable folder)
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name ('development', 'production', 'testing')

    Returns:
        Flask application instance
    """
    # Load environment variables from .env file in the project root
    env_path = os.path.join(BASE_DIR, '.env')
    load_dotenv(env_path)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Register CLI commands
    register_commands(app)

    # Context processors
    register_context_processors(app)

    # Error handlers
    register_error_handlers(app)

    return app


def register_blueprints(app):
    """Register Flask blueprints."""
    from .blueprints.auth import auth_bp
    from .blueprints.cuentas import cuentas_bp
    from .blueprints.asientos import asientos_bp
    from .blueprints.informes import informes_bp
    from .blueprints.ajustes import ajustes_bp
    from .blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cuentas_bp, url_prefix='/cuentas')
    app.register_blueprint(asientos_bp, url_prefix='/asientos')
    app.register_blueprint(informes_bp, url_prefix='/informes')
    app.register_blueprint(ajustes_bp, url_prefix='/ajustes')
    app.register_blueprint(admin_bp, url_prefix='/admin')


def register_commands(app):
    """Register CLI commands."""
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database with tables."""
        db.create_all()
        print('Database tables created.')

    @app.cli.command('create-admin')
    def create_admin():
        """Create default admin user."""
        from .models import Usuario, Empresa

        # Create default company if not exists
        empresa = Empresa.query.filter_by(codigo='DEFAULT').first()
        if not empresa:
            empresa = Empresa(
                codigo='DEFAULT',
                nombre='Empresa Principal',
                activa=True
            )
            db.session.add(empresa)
            db.session.commit()
            print(f'Created default company: {empresa.nombre}')

        # Create admin user if not exists
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            admin = Usuario(
                username='admin',
                nombre='Administrador',
                empresa_id=empresa.id,
                activo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Created admin user (password: admin123)')
        else:
            print('Admin user already exists.')


def register_context_processors(app):
    """Register template context processors."""
    @app.context_processor
    def inject_globals():
        from flask import session, g
        from flask_login import current_user
        from .models import Empresa

        # Get current empresa
        empresa = None
        empresa_id = session.get('empresa_id')
        if empresa_id:
            empresa = Empresa.query.get(empresa_id)
            g.empresa = empresa

        return {
            'app_name': app.config['APP_NAME'],
            'current_user': current_user,
            'empresa_actual': empresa
        }


def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

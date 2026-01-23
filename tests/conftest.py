"""Pytest configuration and fixtures."""
import pytest
from app import create_app, db
from app.models import Usuario, Empresa


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        # Create test empresa
        empresa = Empresa(
            codigo='TEST',
            nombre='Empresa de Prueba',
            activa=True
        )
        db.session.add(empresa)
        db.session.commit()

        # Create test user
        user = Usuario(
            username='testuser',
            nombre='Test User',
            empresa_id=empresa.id,
            activo=True,
            is_admin=True
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        # Login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)

    return client

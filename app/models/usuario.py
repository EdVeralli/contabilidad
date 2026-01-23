"""Usuario model."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class Usuario(UserMixin, db.Model):
    """Model for user authentication and management."""

    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    activo = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    asientos_creados = db.relationship(
        'Asiento',
        foreign_keys='Asiento.usuario_id',
        backref='usuario_creador',
        lazy='dynamic'
    )

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    @property
    def is_active(self):
        """Return whether user is active."""
        return self.activo

    def __repr__(self):
        return f'<Usuario {self.username}>'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'nombre': self.nombre,
            'email': self.email,
            'empresa_id': self.empresa_id,
            'activo': self.activo,
            'is_admin': self.is_admin
        }


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return Usuario.query.get(int(user_id))

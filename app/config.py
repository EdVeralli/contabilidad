"""Application configuration."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Application
    APP_NAME = os.environ.get('APP_NAME', 'Contabilidad')
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))

    # Paths
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DBF_SOURCE_PATH = os.environ.get(
        'DBF_SOURCE_PATH',
        r'C:\APE\VERO_CONTABLE\VERO CONTABLE\CONTA_2'
    )


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    # Use SQLite by default for development (no MySQL needed)
    # Change to MySQL in .env: DATABASE_URL=mysql+pymysql://user:pass@localhost/vero_contable
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(Config.BASE_DIR, 'vero_contable.db')
    )
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ECHO = False

    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

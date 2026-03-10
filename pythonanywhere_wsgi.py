"""WSGI entry point for PythonAnywhere deployment."""
import sys
import os

# Agregar la carpeta del proyecto al path de Python
path = '/home/apecontable/vero_contable'
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar entorno de produccion
os.environ['FLASK_ENV'] = 'production'

from app import create_app
application = create_app('production')

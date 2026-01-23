"""Asientos (Journal Entries) blueprint."""
from flask import Blueprint

asientos_bp = Blueprint('asientos', __name__, template_folder='templates')

from . import routes  # noqa: E402, F401

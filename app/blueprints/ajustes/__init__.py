"""Ajustes (Adjustments) blueprint."""
from flask import Blueprint

ajustes_bp = Blueprint('ajustes', __name__, template_folder='templates')

from . import routes  # noqa: E402, F401

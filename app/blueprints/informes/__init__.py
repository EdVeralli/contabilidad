"""Informes (Reports) blueprint."""
from flask import Blueprint

informes_bp = Blueprint('informes', __name__, template_folder='templates')

from . import routes  # noqa: E402, F401

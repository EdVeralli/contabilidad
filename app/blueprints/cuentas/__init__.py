"""Cuentas (Chart of Accounts) blueprint."""
from flask import Blueprint

cuentas_bp = Blueprint('cuentas', __name__, template_folder='templates')

from . import routes  # noqa: E402, F401

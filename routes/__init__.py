"""
Routing-Modul für die WEG-Abrechnung Anwendung
Enthält alle Blueprint-Module, die in der Hauptanwendung registriert werden
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .transaktionen import transaktionen_bp
from .miteigentuemer import miteigentuemer_bp
from .abrechnung import abrechnung_bp
from .wirtschaftsplan import wirtschaftsplan_bp
from .settings import settings_bp
from .vorlagen import vorlagen_bp
from .setup import setup_bp

# Liste aller Blueprints für die Registrierung in app.py
all_blueprints = [
    auth_bp,
    dashboard_bp,
    transaktionen_bp,
    miteigentuemer_bp,
    abrechnung_bp,
    wirtschaftsplan_bp,
    settings_bp,
    vorlagen_bp,
    setup_bp
]
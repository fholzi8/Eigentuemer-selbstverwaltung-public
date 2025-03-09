"""
Flask-Erweiterungen für die WEG-Abrechnung Anwendung
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# Rate Limiter initialisieren
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Mail initialisieren
mail = Mail()
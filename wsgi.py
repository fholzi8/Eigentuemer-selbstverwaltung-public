"""
WSGI-Einstiegspunkt für Produktionsumgebungen wie PythonAnywhere oder Gunicorn
"""

import sys
import os
import logging
from pathlib import Path

# Pfad zum Projektverzeichnis hinzufügen
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Umgebungsvariable für die Konfiguration setzen
if os.environ.get('FLASK_ENV') != 'development':
    os.environ['FLASK_ENV'] = 'production'

# Anwendung importieren
from app import app as application

# Nach dem Import der Anwendung
from utils.error_handling import setup_global_error_handler
setup_global_error_handler(application)

# Datenbank-Modelle importieren (wichtig für das ORM)
from models import db, User, Miteigentuemer, Transaktion, Wirtschaftsplan, WirtschaftsplanMetadata

# Waitress-Konfiguration
if __name__ == '__main__':
    # Logging-Konfiguration für Waitress
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger('waitress')
    handler = logging.FileHandler('logs/waitress.log')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        from waitress import serve
        print("Starte Waitress-Server...")
        serve(
            application,
            host='0.0.0.0',
            port=8080,
            threads=6,  # Passe an deine Anforderungen an
            url_scheme='http',  # Ändere zu 'https', wenn du HTTPS verwendest
            channel_timeout=30,
            ident='WEG-App Waitress Server'
        )
        print("Waitress-Server gestartet auf http://0.0.0.0:8080")
    except ImportError:
        print("Waitress ist nicht installiert. Verwende den integrierten Flask-Server.")
        application.run(host='0.0.0.0', port=5001)
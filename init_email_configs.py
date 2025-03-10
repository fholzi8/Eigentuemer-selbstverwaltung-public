"""
Skript zur Initialisierung der E-Mail-Konfigurationen aus config.py in der Datenbank
"""

import os
import sys
from flask import Flask

# Pfad zum Projektverzeichnis hinzufügen, falls nötig
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import db, EmailConfiguration
import logging
from datetime import datetime
from config import Config

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Mini-App für die Datenbankinitialisierung erstellen"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def init_email_configs(app):
    """
    Initialisiert die E-Mail-Konfigurationen aus der config.py in der Datenbank
    """
    try:
        with app.app_context():
            # Standard-E-Mail-Einstellungen aus der Config
            email_configs = {
                'MAIL_DEFAULT_SENDER': (app.config.get('MAIL_DEFAULT_SENDER', ''), 'Standard-Absender für E-Mails'),
                'MAIL_NOTIFICATION_SENDER': (app.config.get('MAIL_NOTIFICATION_SENDER', ''), 'Absender für Benachrichtigungen'),
                'MAIL_PASSWORD_RESET_SENDER': (app.config.get('MAIL_PASSWORD_RESET_SENDER', ''), 'Absender für Passwort-Zurücksetzen'),
                'WEG_ARCHIVE_EMAIL': (app.config.get('WEG_ARCHIVE_EMAIL', ''), 'Archiv-E-Mail-Adresse'),
                'MAIL_SERVER': (app.config.get('MAIL_SERVER', ''), 'SMTP-Server'),
                'MAIL_PORT': (str(app.config.get('MAIL_PORT', '')), 'SMTP-Port'),
                'MAIL_USE_TLS': (str(app.config.get('MAIL_USE_TLS', 'False')), 'TLS verwenden'),
                'MAIL_USE_SSL': (str(app.config.get('MAIL_USE_SSL', 'False')), 'SSL verwenden'),
                'MAIL_USERNAME': (app.config.get('MAIL_USERNAME', ''), 'SMTP-Benutzername'),
                'MAIL_PASSWORD': (app.config.get('MAIL_PASSWORD', ''), 'SMTP-Passwort')
            }
            
            # Für jede Konfiguration prüfen, ob sie bereits existiert
            for key, (value, description) in email_configs.items():
                existing = EmailConfiguration.query.filter_by(key=key).first()
                
                if existing:
                    logger.info(f"Konfiguration {key} existiert bereits. Wird aktualisiert.")
                    existing.value = value
                    existing.description = description
                    existing.updated_at = datetime.now()
                else:
                    logger.info(f"Neue Konfiguration {key} wird erstellt.")
                    config = EmailConfiguration(
                        key=key,
                        value=value,
                        description=description,
                        is_active=True
                    )
                    db.session.add(config)
            
            db.session.commit()
            logger.info("E-Mail-Konfigurationen erfolgreich initialisiert.")
            
            # Alle Konfigurationen anzeigen
            all_configs = EmailConfiguration.query.all()
            logger.info(f"Anzahl der Konfigurationen in der Datenbank: {len(all_configs)}")
            for config in all_configs:
                value_display = "********" if "PASSWORD" in config.key else config.value
                logger.info(f"{config.key}: {value_display}")
            
            return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Initialisieren der E-Mail-Konfigurationen: {str(e)}")
        return False

if __name__ == "__main__":
    app = create_app()
    logger.info("Starte Initialisierung der E-Mail-Konfigurationen...")
    success = init_email_configs(app)
    
    if success:
        logger.info("Initialisierung erfolgreich abgeschlossen.")
    else:
        logger.error("Initialisierung fehlgeschlagen.")
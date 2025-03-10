"""
Service-Funktionen für E-Mail-Konfiguration
"""

from models import db, EmailConfiguration
import logging

logger = logging.getLogger(__name__)

def get_all_email_configs():
    """
    Holt alle E-Mail-Konfigurationen
    
    Returns:
        list: Liste von EmailConfiguration-Objekten
    """
    return EmailConfiguration.query.all()

def get_email_config_by_key(key):
    """
    Holt die E-Mail-Konfiguration für einen bestimmten Schlüssel
    
    Args:
        key (str): Konfigurationsschlüssel
        
    Returns:
        EmailConfiguration: Das Konfigurationsobjekt oder None
    """
    return EmailConfiguration.query.filter_by(key=key).first()

def get_email_config_value(key, default=None):
    """
    Holt den Wert einer E-Mail-Konfiguration
    
    Args:
        key (str): Konfigurationsschlüssel
        default: Standardwert, falls key nicht gefunden wird
        
    Returns:
        str: Der Konfigurationswert oder der Standardwert
    """
    config = EmailConfiguration.query.filter_by(key=key, is_active=True).first()
    return config.value if config else default

def set_email_config(key, value, description=None):
    """
    Setzt oder aktualisiert eine E-Mail-Konfiguration
    
    Args:
        key (str): Konfigurationsschlüssel
        value (str): Konfigurationswert
        description (str, optional): Beschreibung der Konfiguration
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Prüfen, ob Konfiguration bereits existiert
        config = EmailConfiguration.query.filter_by(key=key).first()
        
        if config:
            # Aktualisieren
            config.value = value
            if description is not None:
                config.description = description
            config.is_active = True
        else:
            # Neu erstellen
            config = EmailConfiguration(
                key=key,
                value=value,
                description=description,
                is_active=True
            )
            db.session.add(config)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Setzen der E-Mail-Konfiguration: {e}")
        return False

def delete_email_config(key):
    """
    Löscht eine E-Mail-Konfiguration
    
    Args:
        key (str): Konfigurationsschlüssel
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        config = EmailConfiguration.query.filter_by(key=key).first()
        
        if config:
            db.session.delete(config)
            db.session.commit()
            return True
        
        return False  # Konfiguration nicht gefunden
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Löschen der E-Mail-Konfiguration: {e}")
        return False

def initialize_default_email_configs(app_config):
    """
    Initialisiert Standardwerte für E-Mail-Konfigurationen aus der App-Konfiguration
    
    Args:
        app_config: Die Flask-App-Konfiguration
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Standard-E-Mail-Einstellungen aus der Config
        email_configs = {
            'MAIL_DEFAULT_SENDER': (app_config.get('MAIL_DEFAULT_SENDER', ''), 'Standard-Absender für E-Mails'),
            'MAIL_NOTIFICATION_SENDER': (app_config.get('MAIL_NOTIFICATION_SENDER', ''), 'Absender für Benachrichtigungen'),
            'MAIL_PASSWORD_RESET_SENDER': (app_config.get('MAIL_PASSWORD_RESET_SENDER', ''), 'Absender für Passwort-Zurücksetzen'),
            'WEG_ARCHIVE_EMAIL': (app_config.get('WEG_ARCHIVE_EMAIL', ''), 'Archiv-E-Mail-Adresse'),
            'MAIL_SERVER': (app_config.get('MAIL_SERVER', ''), 'SMTP-Server'),
            'MAIL_PORT': (str(app_config.get('MAIL_PORT', '')), 'SMTP-Port'),
            'MAIL_USE_TLS': (str(app_config.get('MAIL_USE_TLS', 'False')), 'TLS verwenden'),
            'MAIL_USE_SSL': (str(app_config.get('MAIL_USE_SSL', 'False')), 'SSL verwenden'),
            'MAIL_USERNAME': (app_config.get('MAIL_USERNAME', ''), 'SMTP-Benutzername'),
            'MAIL_PASSWORD': (app_config.get('MAIL_PASSWORD', ''), 'SMTP-Passwort')
        }
        
        # Für jede Konfiguration prüfen, ob sie bereits existiert
        for key, (value, description) in email_configs.items():
            existing = EmailConfiguration.query.filter_by(key=key).first()
            
            if not existing and value:  # Nur anlegen, wenn noch nicht vorhanden und Wert nicht leer
                config = EmailConfiguration(
                    key=key,
                    value=value,
                    description=description,
                    is_active=True
                )
                db.session.add(config)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Initialisieren der E-Mail-Konfigurationen: {e}")
        return False
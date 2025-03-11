"""
Skript zum Testen der E-Mail-Konfiguration
"""

import os
import sys
from flask import Flask

# Pfad zum Projektverzeichnis hinzufügen
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import Config
from extensions import mail
from models import db, EmailConfiguration  # Importiere die nötigen Modelle
from services.email_config_service import diagnose_email_settings
from utils.email_utils import test_smtp_connection


def create_app():
    """Mini-App für die E-Mail-Tests erstellen"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Lade die E-Mail-Konfigurationen aus der Datenbank
        from services.email_config_service import load_email_configs_to_app
        load_email_configs_to_app(app)
    
    mail.init_app(app)
    return app

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        # 1. Aktuelle Einstellungen anzeigen
        print("\n=== Aktuelle E-Mail-Einstellungen ===")
        diagnose_email_settings()
        
        # 2. SMTP-Verbindung testen
        print("\n=== SMTP-Verbindungstest ===")
        test_smtp_connection()
        
        # 3. Optionales Eingeben eines neuen Passworts zum Testen
        print("\n=== Passwort-Test ===")
        choice = input("Möchtest du ein neues Passwort testen? (j/n): ")
        if choice.lower() == 'j':
            new_password = input("Neues Passwort eingeben: ")
            
            # Temporäres Testen mit manuellen Einstellungen
            print("\n=== Test mit neuem Passwort ===")
            test_settings = {
                'server': app.config.get('MAIL_SERVER'),
                'port': app.config.get('MAIL_PORT'),
                'use_ssl': app.config.get('MAIL_USE_SSL', False),
                'use_tls': app.config.get('MAIL_USE_TLS', False),
                'username': app.config.get('MAIL_USERNAME'),
                'password': new_password,
                'test_recipient': input("Empfänger für Test-E-Mail: ")
            }
            success = test_smtp_connection(use_config=False, manual_settings=test_settings)
            
            if success:
                print("\nDas neue Passwort funktioniert! Möchtest du es in der Datenbank speichern?")
                choice = input("Passwort in Datenbank speichern? (j/n): ")
                if choice.lower() == 'j':
                    from services.email_config_service import set_email_config
                    set_email_config('MAIL_PASSWORD', new_password, 'SMTP-Passwort')
                    print("Passwort in der Datenbank aktualisiert.")
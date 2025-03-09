# test_email.py
from flask import Flask
from flask_mail import Mail, Message
import os
import logging
import argparse
import getpass

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Kommandozeilenargumente parsen
parser = argparse.ArgumentParser(description="Test für E-Mail-Versand")
parser.add_argument('--recipient', '-r', help="E-Mail-Empfänger (falls nicht angegeben, wird die Standard-E-Mail verwendet)")
parser.add_argument('--verbose', '-v', action='store_true', help="Ausführliche Ausgabe")
args = parser.parse_args()

# Test-App erstellen
app = Flask(__name__)

# E-Mail-Konfiguration aus deiner config.py
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'weg.friedrichshafenerstrasse@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'WEG-Verwaltung <weg.friedrichshafenerstrasse@gmail.com>'

# Recipient setzen
recipient = args.recipient or 'weg.friedrichshafenerstrasse@gmail.com'  # Standardmäßig an die eigene Adresse

# Mail-Objekt initialisieren
mail = Mail(app)

def check_config():
    """Überprüft die E-Mail-Konfiguration"""
    print("\n=== E-Mail-Konfiguration ===")
    
    email_config = {
        'MAIL_SERVER': app.config.get('MAIL_SERVER'),
        'MAIL_PORT': app.config.get('MAIL_PORT'),
        'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
        'MAIL_USE_SSL': app.config.get('MAIL_USE_SSL'),
        'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
        'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER')
    }
    
    # Passwort speziell behandeln (nicht anzeigen)
    password_set = bool(app.config.get('MAIL_PASSWORD'))
    
    all_set = True
    for key, value in email_config.items():
        print(f"{key}: {value}")
        if value is None:
            all_set = False
    
    print(f"MAIL_PASSWORD: {'Gesetzt' if password_set else 'NICHT GESETZT'}")
    if not password_set:
        all_set = False
    
    if all_set:
        print("\n✅ Alle Konfigurationseinstellungen sind vorhanden.")
    else:
        print("\n❌ Es fehlen Konfigurationseinstellungen!")
    
    return all_set

def test_email_sending():
    """Testet den E-Mail-Versand"""
    try:
        with app.app_context():
            print(f"\n=== Versende Test-E-Mail an {recipient} ===")
            
            # Wenn kein Passwort vorhanden, interaktiv abfragen
            if not app.config.get('MAIL_PASSWORD'):
                app.config['MAIL_PASSWORD'] = getpass.getpass("MAIL_PASSWORD (wird nicht angezeigt): ")
                if not app.config['MAIL_PASSWORD']:
                    print("❌ Kein Passwort eingegeben. Abbruch.")
                    return False
            
            msg = Message("Test-E-Mail von WEG-App",
                        recipients=[recipient])  
            msg.body = """
Hallo,

dies ist eine Test-E-Mail, um zu prüfen, ob der E-Mail-Versand funktioniert.

Diese E-Mail wurde von test_email.py gesendet.

Mit freundlichen Grüßen
Ihre WEG-App
"""
            msg.html = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
        .content { padding: 20px 0; }
        .footer { font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>WEG-App Test-E-Mail</h2>
        </div>
        <div class="content">
            <p>Hallo,</p>
            <p>dies ist eine Test-E-Mail, um zu prüfen, ob der E-Mail-Versand funktioniert.</p>
            <p>Diese E-Mail wurde von test_email.py gesendet.</p>
        </div>
        <div class="footer">
            <p>Mit freundlichen Grüßen<br>Ihre WEG-App</p>
        </div>
    </div>
</body>
</html>
"""
            mail.send(msg)
            print("✅ E-Mail erfolgreich gesendet!")
            return True
    except Exception as e:
        print(f"❌ Fehler beim Senden der E-Mail: {e}")
        if args.verbose:
            logger.exception("Detaillierter Fehler:")
        return False

if __name__ == "__main__":
    print("=== WEG-App E-Mail-Test ===")
    
    # Konfiguration überprüfen
    config_ok = check_config()
    
    # E-Mail senden, wenn Konfiguration ok oder --force angegeben
    if config_ok:
        test_email_sending()
    else:
        print("\nMöchten Sie trotz fehlender Konfiguration versuchen, eine E-Mail zu senden? (j/n)")
        choice = input().lower()
        if choice in ('j', 'ja', 'y', 'yes'):
            test_email_sending()
        else:
            print("Test abgebrochen.")
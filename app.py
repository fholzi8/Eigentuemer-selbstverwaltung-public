"""
WEG-Abrechnung - Eine Flask-Webanwendung zur Verwaltung von Wohneigentümergemeinschafts-Abrechnungen
"""

from flask import Flask, render_template, request, send_from_directory, g
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_talisman import Talisman
import os
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import secrets

from config import Config
from models import db, User
from routes import all_blueprints
from extensions import limiter, mail
from services.email_config_service import load_email_configs_to_app
from utils.error_handling import setup_global_error_handler

# CSRF-Schutz initialisieren
csrf = CSRFProtect()

# Flask-Anwendung initialisieren
app = Flask(__name__)
app.config.from_object(Config)

# Context Processor für aktuelles Datum/Zeit
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Datenbank initialisieren
db.init_app(app)

# Migration-Extension initialisieren
migrate = Migrate(app, db)

# Extensions initialisieren
csrf.init_app(app)
limiter.init_app(app)

# Nach der Initialisierung aller Extensions
setup_global_error_handler(app)

# Nach der Initialisierung der Datenbank und vor der Initialisierung von Flask-Mail
with app.app_context():
    # Stelle sicher, dass die E-Mail-Konfigurationen geladen werden
    load_email_configs_to_app(app)
    
# Danach mail initialisieren
mail.init_app(app)

# Error-Level/Report für CSP-Verstöße 
@csrf.exempt
@app.route('/logs/csp-report', methods=['POST'])
@limiter.exempt # Vom Rate-Limiting ausnehmen
def csp_report():
    """Logging endpoint for CSP violations"""
    try:
        report = request.get_json(silent=True) or {}
        violation = report.get('csp-report', {})
        if violation:
            app.logger.warning(f"CSP Violation: {violation}")
    except Exception as e:
        app.logger.error(f"Error processing CSP report: {e}")
    return '', 204

# Security Headers Middleware
@app.context_processor
def inject_csp_nonce():
    """Injects a CSP nonce for templates"""
    if not hasattr(g, 'csp_nonce'):
        g.csp_nonce = secrets.token_hex(16)
    return {'csp_nonce': g.csp_nonce}

@app.after_request
def add_security_headers(response):
    # Verwende den gleichen Nonce-Wert aus dem Kontext
    nonce = getattr(g, 'csp_nonce', secrets.token_hex(16))

    # CSP-Policy mit dem Nonce-Wert formatieren
    csp_policy = {}
    for key, value in app.config.get('CSP', {}).items():
        if isinstance(value, str) and '{nonce}' in value:
            csp_policy[key] = value.format(nonce=nonce)
        else:
            csp_policy[key] = value
    
    # Content Security Policy
    if csp_policy:
        response.headers['Content-Security-Policy'] = '; '.join(f"{key} {value}" for key, value in csp_policy.items())
    
    # Weitere wichtige Security Headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

with app.app_context():
    # Stelle sicher, dass alle Tabellen existieren
    db.create_all()

# Stellen Sie sicher, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'rechnungen'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'dokumente'), exist_ok=True)

# Login-Manager initialisieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Bitte melden Sie sich an, um auf diese Seite zuzugreifen."
login_manager.login_message_category = "warning"

# Nach der Initialisierung der Flask-App und anderer Extensions
talisman = Talisman(
    app,
    content_security_policy=None,  # Wir verwalten CSP bereits selbst
    content_security_policy_nonce_in=['script-src', 'style-src'],
    force_https=False,  # Auf True setzen in Produktion
    force_https_permanent=False,
    frame_options='SAMEORIGIN',
    session_cookie_secure=False,  # Auf True setzen in Produktion
    session_cookie_http_only=True,
    referrer_policy='strict-origin-when-cross-origin'
)

# Flask-Login Benutzer-Loader
@login_manager.user_loader
def load_user(user_id):
    # Aktualisierte Version für SQLAlchemy 2.0+ Kompatibilität
    return db.session.get(User, int(user_id))

# Funktion zur Überprüfung der erlaubten Dateitypen
def allowed_file(filename, allowed_extensions=None):
    """
    Prüft, ob ein Dateiname eine erlaubte Endung hat
    
    Args:
        filename (str): Name der Datei
        allowed_extensions (set, optional): Set mit erlaubten Dateierweiterungen.
            Defaults to None (verwendet dann die Konfiguration).
            
    Returns:
        bool: True, wenn die Dateiendung erlaubt ist, sonst False
    """
    if not allowed_extensions:
        allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

# Nach der Initialisierung der App und vor der Registrierung der Blueprints
# Logging-Konfiguration hinzufügen
if not app.debug:
    # Verzeichnis für Logs erstellen, falls es nicht existiert
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Konfiguration des Datei-Handlers mit Rotation
    file_handler = RotatingFileHandler(
        'logs/weg-app.log', 
        maxBytes=10240000,  # ~10MB
        backupCount=20      # Behalte die letzten 20 Log-Dateien
    )
    
    # Log-Format mit Zeitstempel, Loglevel und Codeposition
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Log-Level auf INFO setzen (alles außer DEBUG wird geloggt)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # App-Logger auf INFO-Level setzen
    app.logger.setLevel(logging.INFO)
    app.logger.info('WEG-App startup - {}'.format(datetime.now()))

# Globale Error-Handler für die wichtigsten HTTP-Fehlercodes
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error('404 Fehler: {}'.format(request.path))
    if request.path == '/favicon.ico':
        return render_template('errors/simple_404.html'), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # Rollback bei Datenbankfehlern
    app.logger.error('500 Fehler: {}'.format(error), exc_info=True)
    return render_template('errors/500.html'), 500

# Rate Limiter für besonders sensible Routen
@app.before_request
def limit_login_attempts():
    # Wenn es ein Login-Request ist
    if request.endpoint == 'auth.login' and request.method == 'POST':
        # Zusätzliches Rate-Limiting speziell für Login-Versuche
        limiter.limit("10/hour,3/minute")(lambda: None)()

# Verhindern, dass Suchmaschinen irgendetwas indexieren 
@app.route("/robots.txt")
def robots_txt():
    return "User-agent: *\nDisallow: /", 200, {'Content-Type': 'text/plain'}

# Route für favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Blueprints registrieren
for blueprint in all_blueprints:
    app.register_blueprint(blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
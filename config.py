"""
Konfigurationseinstellungen für die WEG-Abrechnung Anwendung
"""

import os
import secrets
from datetime import timedelta

class Config:
    # Basis-Verzeichnis der Anwendung
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Basis-URL für Links in E-Mails
    BASE_URL = os.environ.get('BASE_URL', 'http://192.168.11.43:5001') 

    # Datenbankeinstellungen
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'weg_abrechnung.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Sicherheitseinstellungen
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Session-Konfiguration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)  # 1 Tag
    SESSION_COOKIE_SECURE = False  # In Produktion auf True setzen
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload-Einstellungen
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf', 'jpg', 'jpeg', 'png'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB maximale Dateigröße
    
    # E-Mail-Konfiguration
    #MAIL_DEFAULT_SENDER = 'WEG-Verwaltung <weg.friedrichshafenerstrasse@gmail.com>'
    #MAIL_NOTIFICATION_SENDER = 'WEG-Benachrichtigungen <weg.friedrichshafenerstrasse+flask@gmail.com>'
    #MAIL_PASSWORD_RESET_SENDER = 'WEG-Sicherheit <weg.friedrichshafenerstrasse+sicherheit@gmail.com>'
    #WEG_ARCHIVE_EMAIL = 'weg.friedrichshafenerstrasse+archiv@gmail.com'
    #MAIL_SERVER = 'smtp.gmail.com'
    # mit STARTTLS
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USE_SSL = False
    # mit SSL
    #MAIL_PORT = 465
    #MAIL_USE_TLS = False
    #MAIL_USE_SSL = True
    #MAIL_USERNAME = 'weg.friedrichshafenerstrasse@gmail.com'
    #MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
   

    # Zeitzone
    TIMEZONE = 'Europe/Berlin'
    
    # Content Security Policy (CSP)
    '''
    CSP = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com",
        'style-src': "'self' 'unsafe-inline' cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        'img-src': "'self' data:",
        'font-src': "'self' cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        'connect-src': "'self'",
        'object-src': "'none'",
        'form-action': "'self'"
    }
    '''
    CSP = {
        'default-src': "'self'",
        'script-src': "'self' 'nonce-{nonce}' cdnjs.cloudflare.com cdn.jsdelivr.net cdn.datatables.net",
        'style-src': "'self' 'nonce-{nonce}' cdnjs.cloudflare.com cdn.jsdelivr.net cdn.datatables.net",
        'img-src': "'self' data:",
        'font-src': "'self' cdnjs.cloudflare.com cdn.jsdelivr.net",
        'connect-src': "'self'",
        'form-action': "'self'",
        'report-uri': '/csp-report'
    }


class DevelopmentConfig(Config):
    DEBUG = True
    BASE_URL = os.environ.get('BASE_URL', 'http://192.168.11.43:5001')
    # Rate Limiting für Entwicklungsumgebung (weniger strikt)
    RATELIMIT_DEFAULT = "200 per minute"
    RATELIMIT_STORAGE_URL = "memory://"
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    BASE_URL = os.environ.get('BASE_URL', 'http://192.168.11.43:5001')
    # Rate Limiting für Tests
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    BASE_URL = os.environ.get('BASE_URL', 'http://192.168.11.43:5001')
    # In Produktionsumgebungen muss immer eine sichere SECRET_KEY gesetzt werden
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production environment")
    
    # Für PythonAnywhere: Stellen Sie sicher, dass die Datenbank im richtigen Verzeichnis liegt
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.BASE_DIR, 'weg_abrechnung.db')
    
    # Sicherheitseinstellungen für Produktion
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting für Produktion (strenger)
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URL = "memory://"  # In Produktion solltest du Redis verwenden, wenn verfügbar
    
    # Content Security Policy für Produktion (strenger)
    CSP = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com",
        'style-src': "'self' 'unsafe-inline' cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        'img-src': "'self' data:",
        'font-src': "'self' cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        'connect-src': "'self'",
        'object-src': "'none'",
        'form-action': "'self'"
    }

# Konfigurationsklassen-Wörterbuch
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    
    'default': DevelopmentConfig
}
"""
Zentrale Fehlerbehandlung für die WEG-App
"""

from flask import current_app, request
from models import db
from services.logging_service import log_error, log_system_event
from flask_login import current_user

def setup_global_error_handler(app):
    """
    Richtet einen globalen Exception-Handler für die Flask-App ein
    """
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Globaler Error-Handler für alle unbehandelten Ausnahmen"""
        # HTTP-Statuscode ermitteln (Standard: 500)
        code = 500
        if hasattr(e, 'code'):
            code = e.code
        
        # User-ID, falls verfügbar
        user_id = None
        if hasattr(current_user, 'id') and current_user.is_authenticated:
            user_id = current_user.id
        
        # Fehlerdetails sammeln
        error_details = {
            'route': request.path,
            'method': request.method,
            'code': code,
            'type': 'system_error'  # Markierung als Systemfehler
        }
        
        # 4xx Fehler als System-Logs mit Level 'warning', 5xx als 'error'
        if 400 <= code < 500:
            log_system_event(
                message=f"HTTP {code}: {str(e)}",
                level='warning',
                details=error_details,
                user_id=user_id
            )
        else:
            # Schwere Fehler als Error-Logs
            log_error(
                message=f"Unbehandelte Ausnahme: {str(e)}",
                exception=e,
                user_id=user_id,
                details=error_details
            )
        
        # Standard Flask-Fehlerbehandlung weitergeben
        return app.handle_exception(e)

def handle_db_error(e, operation, user_id=None, details=None):
    """
    Hilfsfunktion zur Protokollierung von Datenbankfehlern
    """
    # Rollback bei Datenbankfehlern
    db.session.rollback()
    
    # Fehler protokollieren
    error_details = {
        'operation': operation,
        'type': 'database_error'  # Markierung als Datenbankfehler für bessere Filterung
    }
    if details:
        error_details.update(details)
    
    # Als Error-Kategorie mit dem Level 'error' loggen
    from services.logging_service import log_error
    log_error(
        message=f"Datenbankfehler bei '{operation}': {str(e)}",
        exception=e,
        user_id=user_id,
        details=error_details
    )
    
    # Für Debug-Ausgabe in der Konsole
    current_app.logger.error(f"Datenbankfehler bei '{operation}': {str(e)}")
    
    return False
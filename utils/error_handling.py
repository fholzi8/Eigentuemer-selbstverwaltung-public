"""
Zentrale Fehlerbehandlung für die WEG-App
"""

from flask import current_app, request
from models import db
from services.logging_service import log_error
from flask_login import current_user

def setup_global_error_handler(app):
    """
    Richtet einen globalen Exception-Handler für die Flask-App ein
    """
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Globaler Error-Handler für alle Ausnahmen"""
        # Fehler loggen
        
        # Den HTTP-Statuscode ermitteln (Standard: 500)
        code = 500
        if hasattr(e, 'code'):
            code = e.code
        
        # Fehler in unser Logging-System schreiben (nur für schwerwiegende Fehler)
        if code >= 500:
            log_error(
                message=f"Unbehandelte Ausnahme: {str(e)}",
                exception=e,
                user_id=current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None,
                details={
                    'route': request.path,
                    'method': request.method,
                    'code': code
                }
            )
        
        # Standard Flask-Fehlerbehandlung weitergeben
        return app.handle_exception(e)

def handle_db_error(e, operation, user_id=None, details=None):
    """
    Hilfsfunktion zur Protokollierung von Datenbankfehlern
    
    Args:
        e: Die aufgetretene Exception
        operation: Beschreibung der Operation (z.B. "Benutzer erstellen")
        user_id: Optional - ID des aktuellen Benutzers
        details: Optional - Zusätzliche Details als Dictionary
    """
    # Rollback bei Datenbankfehlern
    db.session.rollback()
    
    # Fehler protokollieren
    error_details = {
        'operation': operation
    }
    if details:
        error_details.update(details)
    
    log_error(
        message=f"Datenbankfehler bei '{operation}': {str(e)}",
        exception=e,
        user_id=user_id,
        details=error_details
    )
    
    # Für Debug-Ausgabe in der Konsole
    current_app.logger.error(f"Datenbankfehler bei '{operation}': {str(e)}")
    
    return False  # Rückgabewert für einfaches Prüfen in try/except-Blöcken
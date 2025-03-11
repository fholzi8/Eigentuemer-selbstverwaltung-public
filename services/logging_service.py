"""
Service-Funktionen für das Logging-System
"""

from models import db, LogEntry, User
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

def log_event(category, level, message, details=None, user_id=None):
    """
    Erstellt einen neuen Log-Eintrag
    
    Args:
        category (str): Die Kategorie des Logs ('transaction', 'wirtschaftsplan', 'user', 'error')
        level (str): Der Level des Logs ('info', 'warning', 'error')
        message (str): Die Nachricht des Logs
        details (dict, optional): Zusätzliche Details als Dictionary
        user_id (int, optional): Die ID des Benutzers, der die Aktion ausgeführt hat
    
    Returns:
        LogEntry: Der erstellte Log-Eintrag
    """
    try:
        # Wenn details ein Dictionary ist, konvertieren wir es zu JSON
        details_str = None
        if details:
            if isinstance(details, dict):
                details_str = json.dumps(details)
            else:
                details_str = str(details)
        
        # Log-Eintrag erstellen und speichern
        log_entry = LogEntry(
            timestamp=datetime.now(),
            category=category,
            level=level,
            message=message,
            details=details_str,
            user_id=user_id
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Erstellen des Log-Eintrags: {e}")
        # In diesem Fall loggen wir den Fehler in die Konsole/Datei
        return None

def log_transaction_event(message, transaction=None, user_id=None, level='info', details=None):
    """Helper für Transaktions-Logs"""
    transaction_details = {}
    if transaction:
        transaction_details = {
            'id': transaction.id,
            'datum': transaction.datum.strftime('%Y-%m-%d') if hasattr(transaction, 'datum') else None,
            'beschreibung': transaction.beschreibung if hasattr(transaction, 'beschreibung') else None,
            'betrag': str(transaction.betrag) if hasattr(transaction, 'betrag') else None
        }
    
    if details:
        transaction_details.update(details)
    
    return log_event('transaction', level, message, details=transaction_details, user_id=user_id)

def log_wirtschaftsplan_event(message, wirtschaftsplan=None, user_id=None, level='info', details=None):
    """Helper für Wirtschaftsplan-Logs"""
    wp_details = {}
    if wirtschaftsplan:
        wp_details = {
            'id': wirtschaftsplan.id,
            'jahr': wirtschaftsplan.jahr if hasattr(wirtschaftsplan, 'jahr') else None,
            'bezeichnung': wirtschaftsplan.bezeichnung if hasattr(wirtschaftsplan, 'bezeichnung') else None,
            'betrag': str(wirtschaftsplan.betrag) if hasattr(wirtschaftsplan, 'betrag') else None
        }
    
    if details:
        wp_details.update(details)
    
    return log_event('wirtschaftsplan', level, message, details=wp_details, user_id=user_id)

def log_user_event(message, affected_user=None, user_id=None, level='info', details=None):
    """Helper für Benutzer-Logs"""
    user_details = {}
    if affected_user:
        user_details = {
            'id': affected_user.id,
            'username': affected_user.username if hasattr(affected_user, 'username') else None
        }
    
    if details:
        user_details.update(details)
    
    return log_event('user', level, message, details=user_details, user_id=user_id)

def log_error(message, exception=None, user_id=None, details=None):
    """Helper für Fehler-Logs"""
    error_details = {}
    if exception:
        error_details = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception)
        }
    
    if details:
        error_details.update(details)
    
    return log_event('error', 'error', message, details=error_details, user_id=user_id)

def get_logs(category=None, level=None, limit=100, offset=0, start_date=None, end_date=None, user_id=None):
    """
    Holt Log-Einträge mit verschiedenen Filtern
    
    Args:
        category (str, optional): Filtert nach Kategorie
        level (str, optional): Filtert nach Level
        limit (int, optional): Maximale Anzahl an Einträgen
        offset (int, optional): Offset für Paginierung
        start_date (datetime, optional): Filtert nach Datum >= start_date
        end_date (datetime, optional): Filtert nach Datum <= end_date
        user_id (int, optional): Filtert nach Benutzer-ID
    
    Returns:
        tuple: (logs, total_count)
    """
    query = LogEntry.query
    
    # Filter anwenden
    if category:
        query = query.filter(LogEntry.category == category)
    
    if level:
        query = query.filter(LogEntry.level == level)
    
    if start_date:
        query = query.filter(LogEntry.timestamp >= start_date)
    
    if end_date:
        query = query.filter(LogEntry.timestamp <= end_date)
    
    if user_id:
        query = query.filter(LogEntry.user_id == user_id)
    
    # Gesamtzahl der Logs berechnen
    total_count = query.count()
    
    # Sortierung und Limit anwenden
    logs = query.order_by(LogEntry.timestamp.desc())
    
    if limit > 0:
        logs = logs.offset(offset).limit(limit)
    
    return logs.all(), total_count
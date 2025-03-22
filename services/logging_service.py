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

def set_log_retention_days(days):
    """Setzt die Anzahl der Tage, für die Logs aufbewahrt werden sollen"""
    from models import db, SystemSettings
    
    setting = SystemSettings.query.filter_by(key='log_retention_days').first()
    if setting:
        setting.value = str(days)
    else:
        setting = SystemSettings(
            key='log_retention_days',
            value=str(days),
            description='Anzahl der Tage, für die Logs aufbewahrt werden'
        )
        db.session.add(setting)
    
    db.session.commit()
    return True

def get_log_retention_days():
    """Gibt die Anzahl der Tage zurück, für die Logs aufbewahrt werden"""
    from models import SystemSettings
    
    days = SystemSettings.get_value('log_retention_days', '30')  # Standard: 30 Tage
    return int(days)

def cleanup_old_logs():
    """Löscht Logs, die älter als die eingestellte Retention Period sind"""
    from models import db, LogEntry
    from datetime import datetime, timedelta
    
    retention_days = get_log_retention_days()
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    # Logs löschen, die älter als das Cutoff-Datum sind
    deleted_count = LogEntry.query.filter(LogEntry.timestamp < cutoff_date).delete()
    
    db.session.commit()
    return deleted_count

def schedule_log_cleanup():
    """Plant die regelmäßige Bereinigung alter Logs"""
    from services.logging_service import cleanup_old_logs
    from datetime import datetime
    from models import SystemSettings
    
    # Letzten Cleanup-Zeitpunkt prüfen
    last_cleanup = SystemSettings.get_value('last_log_cleanup')
    if last_cleanup:
        last_cleanup_date = datetime.strptime(last_cleanup, '%Y-%m-%d')
        today = datetime.now().date()
        
        # Nur einmal täglich bereinigen
        if (today - last_cleanup_date.date()).days < 1:
            return
    
    # Alte Logs bereinigen
    deleted_count = cleanup_old_logs()
    
    # Zeitpunkt des letzten Cleanups speichern
    from models import db, SystemSettings
    
    setting = SystemSettings.query.filter_by(key='last_log_cleanup').first()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if setting:
        setting.value = today_str
    else:
        setting = SystemSettings(
            key='last_log_cleanup',
            value=today_str,
            description='Datum der letzten Log-Bereinigung'
        )
        db.session.add(setting)
    
    db.session.commit()
    
    # Log-Eintrag über die erfolgreiche Bereinigung
    if deleted_count > 0:
        from services.logging_service import log_system_event
        log_system_event(
            message=f'Automatische Log-Bereinigung: {deleted_count} alte Einträge wurden gelöscht.',
            category='system',
            level='info'
        )

def log_system_event(message, level='info', details=None, user_id=None):
    """Helper für System-Logs"""
    system_details = {}
    
    if details:
        system_details.update(details)
    
    return log_event('system', level, message, details=system_details, user_id=user_id)
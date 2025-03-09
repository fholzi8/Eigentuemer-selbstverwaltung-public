"""
Service-Funktionen für Kontostände
"""

from decimal import Decimal
import datetime
import logging

from models import db, Kontostand, Transaktion

logger = logging.getLogger(__name__)

def get_current_kontostand():
    """
    Gibt den aktuellsten Kontostand zurück
    
    Returns:
        Decimal: Aktueller Kontostand oder 0 wenn nichts gefunden
    """
    latest = Kontostand.query.order_by(Kontostand.datum.desc()).first()
    return latest.betrag if latest else Decimal('0.00')

def get_kontostand_history(limit=10):
    """
    Gibt die Historie der Kontostände zurück
    
    Args:
        limit (int): Anzahl der zurückzugebenden Einträge, 0 für alle
    
    Returns:
        list: Liste der Kontostand-Einträge
    """
    query = Kontostand.query.order_by(Kontostand.datum.desc())
    
    if limit > 0:
        query = query.limit(limit)
    
    return query.all()

def create_kontostand(datum, betrag, kommentar="", user_id=None):
    """
    Erstellt einen neuen Kontostand-Eintrag
    
    Args:
        datum (datetime.date): Datum des Kontostands
        betrag (Decimal): Betrag des Kontostands
        kommentar (str, optional): Optionaler Kommentar. Defaults to "".
        user_id (int, optional): ID des Benutzers. Defaults to None.
    
    Returns:
        tuple: (success, message, kontostand)
    """
    try:
        kontostand = Kontostand(
            datum=datum,
            betrag=betrag,
            kommentar=kommentar,
            user_id=user_id
        )
        
        db.session.add(kontostand)
        db.session.commit()
        
        return True, "Kontostand erfolgreich erstellt", kontostand
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Erstellen des Kontostands: {e}")
        return False, str(e), None

def delete_kontostand(kontostand_id):
    """
    Löscht einen Kontostand-Eintrag
    
    Args:
        kontostand_id (int): ID des zu löschenden Kontostands
    
    Returns:
        tuple: (success, message)
    """
    try:
        kontostand = Kontostand.query.get(kontostand_id)
        
        if not kontostand:
            return False, "Kontostand nicht gefunden"
        
        db.session.delete(kontostand)
        db.session.commit()
        
        return True, "Kontostand erfolgreich gelöscht"
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Löschen des Kontostands: {e}")
        return False, str(e)

def calculate_theoretical_kontostand(to_date=None):
    """
    Berechnet den theoretischen Kontostand basierend auf allen Transaktionen
    
    Args:
        to_date (datetime.date, optional): Datum, bis zu dem berechnet werden soll. Defaults to None.
    
    Returns:
        Decimal: Berechneter Kontostand
    """
    query = Transaktion.query
    
    if to_date:
        query = query.filter(Transaktion.datum <= to_date)
    
    summe = query.with_entities(db.func.sum(Transaktion.betrag)).scalar() or Decimal('0.00')
    
    return summe
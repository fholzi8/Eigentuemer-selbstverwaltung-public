"""
Service-Funktionen für Kategorie-Kostenart-Mapping
"""

from models import db, KategorieKostenartMapping
import logging

logger = logging.getLogger(__name__)

def get_all_mappings():
    """
    Holt alle Kategorie-Kostenart-Mappings
    
    Returns:
        dict: Dictionary mit Wirtschaftsplankategorien als Schlüssel und Listen von Transaktionskostenarten als Werte
    """
    mappings = KategorieKostenartMapping.query.all()
    result = {}
    
    for mapping in mappings:
        if mapping.wp_kategorie not in result:
            result[mapping.wp_kategorie] = []
        result[mapping.wp_kategorie].append(mapping.tx_kostenart)
    
    return result

def get_kostenarten_for_kategorie(kategorie):
    """
    Holt alle zugeordneten Kostenarten für eine Wirtschaftsplankategorie
    
    Args:
        kategorie (str): Wirtschaftsplankategorie
        
    Returns:
        list: Liste der zugeordneten Transaktionskostenarten
    """
    mappings = KategorieKostenartMapping.query.filter_by(wp_kategorie=kategorie).all()
    return [mapping.tx_kostenart for mapping in mappings]

def get_kategorie_for_kostenart(kostenart):
    """
    Holt die zugeordnete Wirtschaftsplankategorie für eine Transaktionskostenart
    
    Args:
        kostenart (str): Transaktionskostenart
        
    Returns:
        str: Zugeordnete Wirtschaftsplankategorie oder None
    """
    mapping = KategorieKostenartMapping.query.filter_by(tx_kostenart=kostenart).first()
    return mapping.wp_kategorie if mapping else None

def add_mapping(wp_kategorie, tx_kostenart):
    """
    Fügt ein neues Mapping hinzu
    
    Args:
        wp_kategorie (str): Wirtschaftsplankategorie
        tx_kostenart (str): Transaktionskostenart
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Prüfen, ob Mapping bereits existiert
        existing = KategorieKostenartMapping.query.filter_by(
            wp_kategorie=wp_kategorie, 
            tx_kostenart=tx_kostenart
        ).first()
        
        if existing:
            return True  # Mapping existiert bereits
        
        mapping = KategorieKostenartMapping(
            wp_kategorie=wp_kategorie,
            tx_kostenart=tx_kostenart
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Hinzufügen des Mappings: {e}")
        return False

def delete_mapping(wp_kategorie, tx_kostenart):
    """
    Löscht ein Mapping
    
    Args:
        wp_kategorie (str): Wirtschaftsplankategorie
        tx_kostenart (str): Transaktionskostenart
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        mapping = KategorieKostenartMapping.query.filter_by(
            wp_kategorie=wp_kategorie, 
            tx_kostenart=tx_kostenart
        ).first()
        
        if mapping:
            db.session.delete(mapping)
            db.session.commit()
            return True
        
        return False  # Mapping nicht gefunden
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Löschen des Mappings: {e}")
        return False
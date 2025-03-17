"""
Service-Funktionen für Vorlagen
"""

from models import db, BriefVorlage, TagesordnungspunktVorlage, WichtigesDokument
from sqlalchemy import desc

def get_brief_vorlagen(filter_typ=None):
    """
    Liefert gefilterte Brief-Vorlagen zurück
    
    Args:
        filter_typ (str): Filter für Vorlagentyp (Eigentümerversammlung, Umlaufbeschluss, Rundschreiben)
    
    Returns:
        List: Liste der gefilterten Brief-Vorlagen
    """
    query = BriefVorlage.query
    
    if filter_typ:
        query = query.filter_by(typ=filter_typ)
    
    return query.order_by(BriefVorlage.titel).all()

def get_tops(filter_status='aktiv'):
    """
    Liefert gefilterte Tagesordnungspunkte zurück
    
    Args:
        filter_status (str): Filter für Status (aktiv, archiviert, entwurf)
    
    Returns:
        List: Liste der gefilterten Tagesordnungspunkte
    """
    query = TagesordnungspunktVorlage.query
    
    if filter_status != 'alle':
        query = query.filter_by(status=filter_status)
    
    return query.order_by(TagesordnungspunktVorlage.position).all()

def get_wichtige_dokumente(filter_kategorie=None):
    """
    Liefert gefilterte wichtige Dokumente zurück
    
    Args:
        filter_kategorie (str): Filter für Dokumentenkategorie
    
    Returns:
        List: Liste der gefilterten wichtigen Dokumente
    """
    query = WichtigesDokument.query
    
    if filter_kategorie:
        query = query.filter_by(kategorie=filter_kategorie)
    
    return query.order_by(WichtigesDokument.kategorie, WichtigesDokument.titel).all()
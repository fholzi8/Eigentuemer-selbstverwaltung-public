"""
Service-Funktionen für Transaktionen
"""

from models import db, Transaktion

def get_filtered_transaktionen(page, filter_kostenart, filter_umlagefaehig, filter_verteilungsschluessel, filter_transaktionstyp, filter_jahr):
    """
    Liefert gefilterte Transaktionen basierend auf den übergebenen Filtern
    
    Args:
        page (int): Aktuelle Seite für Pagination
        filter_kostenart (str): Filter für Kostenart
        filter_umlagefaehig (str): Filter für umlagefähige Kosten (ja/nein)
        filter_verteilungsschluessel (str): Filter für Verteilungsschlüssel
        filter_transaktionstyp (str): Filter für Transaktionstyp (einzahlungen/ausgaben)
        filter_jahr (int): Filter für Jahr
    
    Returns:
        Pagination: Paginierte Liste der gefilterten Transaktionen
    """
    # Filter erstellen
    query = Transaktion.query.filter(Transaktion.jahr == filter_jahr)
    
    # Filter für Transaktionstyp (Einzahlungen/Ausgaben)
    if filter_transaktionstyp == 'einzahlungen':
        query = query.filter(Transaktion.betrag > 0)
    elif filter_transaktionstyp == 'ausgaben':
        query = query.filter(Transaktion.betrag < 0)
    
    if filter_kostenart:
        query = query.filter(Transaktion.kostenart == filter_kostenart)
    
    if filter_umlagefaehig:
        umlagefaehig_bool = (filter_umlagefaehig == 'ja')
        query = query.filter(Transaktion.umlagefaehig == umlagefaehig_bool)
    
    if filter_verteilungsschluessel:
        query = query.filter(Transaktion.verteilungsschluessel == filter_verteilungsschluessel)
    
    # Sortieren und paginieren
    return query.order_by(Transaktion.datum.desc()).paginate(page=page, per_page=20, error_out=False)

def get_transaction_statistics(jahr):
    """
    Berechnet Statistiken über Transaktionen für ein bestimmtes Jahr
    
    Args:
        jahr (int): Jahr für die Statistiken
    
    Returns:
        dict: Statistiken zu Einnahmen und Ausgaben
    """
    # Summe der Einnahmen
    summe_einnahmen = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag > 0, 
        Transaktion.jahr == jahr,
        # Nur Transaktionen mit bestimmten Kostenarten einbeziehen
        Transaktion.kostenart.in_(['Einzahlung', 'Hausgeld', 'Sonderumlage']) 
    ).scalar() or 0
    
    # Summe der Ausgaben
    summe_ausgaben = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0, 
        Transaktion.jahr == jahr
    ).scalar() or 0
    
    # Umlagefähige Kosten
    summe_umlagefaehig = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.jahr == jahr
    ).scalar() or 0
    
    return {
        'summe_einnahmen': summe_einnahmen,
        'summe_ausgaben': summe_ausgaben,
        'summe_umlagefaehig': summe_umlagefaehig
    }
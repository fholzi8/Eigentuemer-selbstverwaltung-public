"""
Service-Funktionen für Vorlagen
"""

from models import db, BriefVorlage, TagesordnungspunktVorlage, WichtigesDokument
from models import BriefVorlage, Miteigentuemer, Selbstverwaltung
from utils.email import send_email
import datetime
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

def send_template_email(vorlage_id, miteigentuemer_ids=None, subject=None, sender=None):
    """
    Sendet eine Brief-Vorlage als E-Mail an Miteigentümer
    
    Args:
        vorlage_id (int): ID der Brief-Vorlage
        miteigentuemer_ids (list, optional): Liste der Miteigentümer-IDs, an die gesendet werden soll
                                           Wenn None, werden alle Miteigentümer mit E-Mail verwendet
        subject (str, optional): Betreffzeile der E-Mail, sonst wird der Vorlagentitel verwendet
        sender (str, optional): Absender-E-Mail

    Returns:
        dict: Ergebnis des Versands {'success': bool, 'sent': Anzahl, 'failed': Anzahl, 'message': str}
    """
    
    result = {'success': False, 'sent': 0, 'failed': 0, 'message': ''}
    
    try:
        # Brief-Vorlage laden
        vorlage = BriefVorlage.query.get(vorlage_id)
        if not vorlage:
            result['message'] = 'Brief-Vorlage nicht gefunden'
            return result
            
        # Selbstverwaltungsdaten laden
        selbstverwaltung = Selbstverwaltung.query.first()
        
        # Miteigentümer filtern
        if miteigentuemer_ids:
            miteigentuemer_list = Miteigentuemer.query.filter(
                Miteigentuemer.id.in_(miteigentuemer_ids), 
                Miteigentuemer.email.isnot(None)
            ).all()
        else:
            miteigentuemer_list = Miteigentuemer.query.filter(
                Miteigentuemer.email.isnot(None)
            ).all()
            
        if not miteigentuemer_list:
            result['message'] = 'Keine Miteigentümer mit E-Mail-Adresse gefunden'
            return result
            
        # Betreff vorbereiten
        email_subject = subject or f"WEG-Info: {vorlage.titel}"
        
        # E-Mails senden
        for miteigentuemer in miteigentuemer_list:
            if not miteigentuemer.email:
                continue
                
            # Vorlage für diesen Miteigentümer personalisieren
            personalized_content = personalize_template(vorlage.inhalt, miteigentuemer, selbstverwaltung)
            
            # E-Mail senden
            success = send_email(
                subject=email_subject,
                recipients=[miteigentuemer.email],
                template='brief_email',
                sender=sender,
                title=vorlage.titel,
                content=personalized_content,
                miteigentuemer=miteigentuemer,
                selbstverwaltung=selbstverwaltung
            )
            
            if success:
                result['sent'] += 1
            else:
                result['failed'] += 1
                
        result['success'] = result['sent'] > 0
        result['message'] = f"{result['sent']} E-Mails gesendet, {result['failed']} fehlgeschlagen"
        
        return result
    except Exception as e:
        result['message'] = f"Fehler beim Versenden der E-Mails: {str(e)}"
        return result
        
def personalize_template(template_content, miteigentuemer, selbstverwaltung=None):
    """
    Ersetzt Platzhalter in einer Vorlage mit den Daten eines Miteigentümers
    
    Args:
        template_content (str): Vorlageninhalt mit Platzhaltern
        miteigentuemer (Miteigentuemer): Miteigentümer-Objekt
        selbstverwaltung (Selbstverwaltung, optional): Selbstverwaltungs-Objekt
        
    Returns:
        str: Personalisierter Vorlageninhalt
    """
    import datetime
    
    # Kopie des Vorlageninhalt erstellen
    content = template_content
    
    # Datum ersetzen
    content = content.replace('{{datum}}', datetime.datetime.now().strftime('%d.%m.%Y'))
    
    # Miteigentümer-Daten ersetzen
    if miteigentuemer:
        content = content.replace('{{name}}', miteigentuemer.name or '')
        content = content.replace('{{mea}}', str(miteigentuemer.mea or ''))
        content = content.replace('{{strasse}}', miteigentuemer.strasse or '')
        content = content.replace('{{plz}}', miteigentuemer.plz or '')
        content = content.replace('{{ort}}', miteigentuemer.ort or '')
    
    # Selbstverwaltungsdaten ersetzen
    if selbstverwaltung:
        content = content.replace('{{weg_name}}', selbstverwaltung.name or '')
        content = content.replace('{{adresse}}', selbstverwaltung.adresse or '')
        content = content.replace('{{plz}}', selbstverwaltung.plz or '')
        content = content.replace('{{ort}}', selbstverwaltung.ort or '')
        content = content.replace('{{verwalter}}', selbstverwaltung.verwalter or '')
        content = content.replace('{{beirat}}', selbstverwaltung.beirat_vorsitz or '')
        content = content.replace('{{beisitzer}}', selbstverwaltung.beisitzer or '')
    
    return content
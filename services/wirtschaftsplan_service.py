"""
Service-Funktionen für Wirtschaftspläne
"""

import pandas as pd
import os
from datetime import datetime
from decimal import Decimal
import logging

from models import db, Wirtschaftsplan, WirtschaftsplanMetadata, Miteigentuemer, Transaktion
from utils import allowed_file, parse_german_date 
from services.kategorie_mapping_service import get_all_mappings, get_kategorie_for_kostenart

logger = logging.getLogger(__name__)

def get_wirtschaftsplan_data(jahr):
    """
    Holt alle Wirtschaftsplan-Daten für ein Jahr
    
    Args:
        jahr (int): Jahr des Wirtschaftsplans
        
    Returns:
        dict: Enthält Wirtschaftsplan-Einträge, Metadaten und Summen
    """
    # Einträge abfragen
    eintraege = Wirtschaftsplan.query.filter_by(jahr=jahr).order_by(Wirtschaftsplan.kategorie).all()
    
    # Metadaten abfragen
    metadata = WirtschaftsplanMetadata.query.filter_by(jahr=jahr).first()
    
    # Summen berechnen
    summe_gesamt = sum(eintrag.betrag for eintrag in eintraege)
    
    summe_umlagefaehig = sum(eintrag.betrag for eintrag in eintraege if eintrag.umlagefaehig)
    summe_nicht_umlagefaehig = summe_gesamt - summe_umlagefaehig
    
    summe_einheiten = sum(eintrag.betrag for eintrag in eintraege if eintrag.verteilungsschluessel == 'Einheiten')
    summe_vf = sum(eintrag.betrag for eintrag in eintraege if eintrag.verteilungsschluessel == 'VF-Einheiten')
    summe_tg = sum(eintrag.betrag for eintrag in eintraege if eintrag.verteilungsschluessel == 'TG-Einheiten')
    
    # Gruppierte Daten nach Kategorie
    kategorien = {}
    for eintrag in eintraege:
        kategorie = eintrag.kategorie or 'Sonstige'
        if kategorie not in kategorien:
            kategorien[kategorie] = []
        kategorien[kategorie].append(eintrag)
    
    # Miteigentümeranteile berechnen
    miteigentuemer = Miteigentuemer.query.all()
    miteigentuemer_anteile = []
    
    # Summen für Verteilungsschlüssel
    summe_m_einheiten = sum(m.einheiten for m in miteigentuemer) if miteigentuemer else 1
    summe_m_vf = sum(m.vf_einheiten for m in miteigentuemer) if miteigentuemer else 1
    summe_m_tg = sum(m.tg_einheiten for m in miteigentuemer) if miteigentuemer else 1
    
    for m in miteigentuemer:
        # Anteile berechnen
        anteil_einheiten = Decimal(str(m.einheiten / summe_m_einheiten)) * summe_einheiten if summe_m_einheiten > 0 else Decimal('0')
        
        anteil_vf = Decimal('0')
        if m.vf_einheiten > 0 and summe_m_vf > 0:
            anteil_vf = Decimal(str(m.vf_einheiten / summe_m_vf)) * summe_vf
        
        anteil_tg = Decimal('0')
        if m.tg_einheiten > 0 and summe_m_tg > 0:
            anteil_tg = Decimal(str(m.tg_einheiten / summe_m_tg)) * summe_tg
        
        gesamt_anteil = anteil_einheiten + anteil_vf + anteil_tg
        
        miteigentuemer_anteile.append({
            'miteigentuemer': m,
            'anteil_einheiten': anteil_einheiten,
            'anteil_vf': anteil_vf,
            'anteil_tg': anteil_tg,
            'gesamt_anteil': gesamt_anteil
        })
    
    return {
        'eintraege': eintraege,
        'kategorien': kategorien,
        'metadata': metadata,
        'summen': {
            'gesamt': summe_gesamt,
            'umlagefaehig': summe_umlagefaehig,
            'nicht_umlagefaehig': summe_nicht_umlagefaehig,
            'einheiten': summe_einheiten,
            'vf': summe_vf,
            'tg': summe_tg
        },
        'miteigentuemer_anteile': miteigentuemer_anteile
    }

def import_wirtschaftsplan(file_path, jahr, user_id):
    """
    Importiert einen Wirtschaftsplan aus einer Excel- oder CSV-Datei
    
    Args:
        file_path (str): Pfad zur Datei
        jahr (int): Jahr des Wirtschaftsplans
        user_id (int): ID des Benutzers, der den Import durchführt
        
    Returns:
        tuple: (success, message, count), wobei success ein Boolean ist, message eine Nachricht und count die Anzahl der importierten Einträge
    """
    try:
        # Dateierweiterung prüfen
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Excel-Datei
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        # CSV-Datei
        else:
            # Versuchen, CSV zu lesen mit verschiedenen Encodings und Separatoren
            try:
                df = pd.read_csv(file_path, sep=';', encoding='utf-8', decimal=',')
            except:
                try:
                    df = pd.read_csv(file_path, sep=',', encoding='utf-8')
                except:
                    df = pd.read_csv(file_path, sep=';', encoding='latin1', decimal=',')
        
        # Spalten prüfen
        required_columns = ['bezeichnung', 'betrag']
        for col in required_columns:
            if col not in df.columns:
                return False, f"Die Spalte '{col}' fehlt in der Datei", 0
        
        # Optionale Spalten mit Standardwerten
        if 'kategorie' not in df.columns:
            df['kategorie'] = 'Sonstige'
        if 'verteilungsschluessel' not in df.columns:
            df['verteilungsschluessel'] = 'Einheiten'
        if 'umlagefaehig' not in df.columns:
            df['umlagefaehig'] = False
        if 'notiz' not in df.columns:
            df['notiz'] = ''
        
        # Betrag als Dezimalzahl konvertieren
        if df['betrag'].dtype == object:
            df['betrag'] = df['betrag'].str.replace('.', '').str.replace(',', '.').astype(float)
        
        # Erstellen/Aktualisieren der Metadaten
        metadata = WirtschaftsplanMetadata.query.filter_by(jahr=jahr).first()
        if not metadata:
            metadata = WirtschaftsplanMetadata(
                jahr=jahr,
                importiert_am=datetime.now(),
                importiert_von=user_id,
                dateiname=os.path.basename(file_path),
                status="aktiv"
            )
            db.session.add(metadata)
        else:
            metadata.importiert_am = datetime.now()
            metadata.importiert_von = user_id
            metadata.dateiname = os.path.basename(file_path)
        
        # Alte Einträge löschen (optional, je nach Anforderung)
        # Wirtschaftsplan.query.filter_by(jahr=jahr).delete()
        
        # Neue Einträge erstellen
        count = 0
        for _, row in df.iterrows():
            eintrag = Wirtschaftsplan(
                jahr=jahr,
                bezeichnung=row['bezeichnung'],
                kategorie=row['kategorie'],
                betrag=Decimal(str(row['betrag'])),
                verteilungsschluessel=row['verteilungsschluessel'],
                umlagefaehig=bool(row['umlagefaehig']),
                notiz=str(row['notiz'])
            )
            db.session.add(eintrag)
            count += 1
        
        # Änderungen speichern
        db.session.commit()
        
        return True, "Import erfolgreich", count
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Importieren des Wirtschaftsplans: {e}")
        return False, str(e), 0

def calculate_wirtschaftsplan_anteile(jahr, miteigentuemer_id=None):
    """
    Berechnet die Anteile eines Miteigentümers (oder aller) am Wirtschaftsplan
    
    Args:
        jahr (int): Jahr des Wirtschaftsplans
        miteigentuemer_id (int, optional): Optional, wenn nur für einen Miteigentümer berechnet werden soll
        
    Returns:
        dict: Berechnete Anteile für jeden Miteigentümer oder für einen bestimmten Miteigentümer
    """
    # Wirtschaftsplan-Einträge abfragen
    eintraege = Wirtschaftsplan.query.filter_by(jahr=jahr).all()
    
    # Miteigentümer abfragen
    if miteigentuemer_id:
        miteigentuemer_liste = [Miteigentuemer.query.get(miteigentuemer_id)]
        if not miteigentuemer_liste[0]:
            return None
    else:
        miteigentuemer_liste = Miteigentuemer.query.all()
    
    # Summen nach Verteilungsschlüssel
    summe_einheiten = sum(e.betrag for e in eintraege if e.verteilungsschluessel == 'Einheiten')
    summe_vf = sum(e.betrag for e in eintraege if e.verteilungsschluessel == 'VF-Einheiten')
    summe_tg = sum(e.betrag for e in eintraege if e.verteilungsschluessel == 'TG-Einheiten')
    
    # Summe aller Einheiten der Miteigentümer
    gesamt_einheiten = sum(m.einheiten for m in miteigentuemer_liste)
    gesamt_vf = sum(m.vf_einheiten for m in miteigentuemer_liste)
    gesamt_tg = sum(m.tg_einheiten for m in miteigentuemer_liste)
    
    # Anteile berechnen
    result = {}
    for m in miteigentuemer_liste:
        # Anteil Einheiten
        anteil_einheiten = Decimal('0')
        if gesamt_einheiten > 0:
            anteil_einheiten = (Decimal(str(m.einheiten)) / Decimal(str(gesamt_einheiten))) * summe_einheiten
        
        # Anteil VF
        anteil_vf = Decimal('0')
        if gesamt_vf > 0 and m.vf_einheiten > 0:
            anteil_vf = (Decimal(str(m.vf_einheiten)) / Decimal(str(gesamt_vf))) * summe_vf
        
        # Anteil TG
        anteil_tg = Decimal('0')
        if gesamt_tg > 0 and m.tg_einheiten > 0:
            anteil_tg = (Decimal(str(m.tg_einheiten)) / Decimal(str(gesamt_tg))) * summe_tg
        
        # Gesamtanteil
        gesamt_anteil = anteil_einheiten + anteil_vf + anteil_tg
        
        result[m.id] = {
            'miteigentuemer': m,
            'anteil_einheiten': anteil_einheiten,
            'anteil_vf': anteil_vf,
            'anteil_tg': anteil_tg,
            'gesamt_anteil': gesamt_anteil
        }
    
    if miteigentuemer_id:
        return result.get(miteigentuemer_id)
    
    return result

def activate_wirtschaftsplan(jahr):
    """
    Aktiviert einen Wirtschaftsplan für ein bestimmtes Jahr
    
    Args:
        jahr (int): Jahr des zu aktivierenden Wirtschaftsplans
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Aktuellen aktiven Wirtschaftsplan für das Jahr holen
        metadata = WirtschaftsplanMetadata.query.filter_by(jahr=jahr).first()
        
        if not metadata:
            return False
        
        metadata.status = 'aktiv'
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Aktivieren des Wirtschaftsplans: {e}")
        return False

def archive_wirtschaftsplan(jahr):
    """
    Archiviert einen Wirtschaftsplan für ein bestimmtes Jahr
    
    Args:
        jahr (int): Jahr des zu archivierenden Wirtschaftsplans
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Aktuellen aktiven Wirtschaftsplan für das Jahr holen
        metadata = WirtschaftsplanMetadata.query.filter_by(jahr=jahr).first()
        
        if not metadata:
            return False
        
        metadata.status = 'archiviert'
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Archivieren des Wirtschaftsplans: {e}")
        return False


def get_actual_costs(jahr):
    """
    Ermittelt die tatsächlichen Kosten für ein Jahr aus den Transaktionen,
    gruppiert nach Kostenarten und Verteilungsschlüsseln für den Vergleich mit dem Wirtschaftsplan
    """
    
    logger = logging.getLogger(__name__)
    
    # Debug Punkt 1
    #print(f"DEBUG: Jahr {jahr}")
    
    # Kategorie-Kostenart-Mappings holen
    kategorie_mappings = get_all_mappings()
    #print(f"DEBUG: Mappings {kategorie_mappings}")
    
    # Alle Ausgaben für das Jahr abfragen (nur negative Beträge)
    transaktionen = Transaktion.query.filter(
        Transaktion.jahr == jahr,
        Transaktion.betrag < 0  # Nur Ausgaben (negative Beträge)
    ).all()
    
    #print(f"DEBUG: Anzahl Transaktionen für Jahr {jahr}: {len(transaktionen)}")
    
    # Summen berechnen
    summe_gesamt = sum(abs(t.betrag) for t in transaktionen)
    
    summe_umlagefaehig = sum(abs(t.betrag) for t in transaktionen if t.umlagefaehig)
    summe_nicht_umlagefaehig = summe_gesamt - summe_umlagefaehig
    
    summe_einheiten = sum(abs(t.betrag) for t in transaktionen if t.verteilungsschluessel == 'Einheiten')
    summe_vf = sum(abs(t.betrag) for t in transaktionen if t.verteilungsschluessel == 'VF-Einheiten')
    summe_tg = sum(abs(t.betrag) for t in transaktionen if t.verteilungsschluessel == 'TG-Einheiten')
    
    # Gruppiere nach Kostenart
    kostenarten = {}
    for transaktion in transaktionen:
        kostenart = transaktion.kostenart or 'Sonstige'
        if kostenart not in kostenarten:
            kostenarten[kostenart] = []
        kostenarten[kostenart].append(transaktion)
    
    # Berechne Summen für jede Kostenart
    kostenarten_summen = {}
    for kostenart, tx_list in kostenarten.items():
        kostenarten_summen[kostenart] = sum(abs(t.betrag) for t in tx_list)
    
    #print(f"DEBUG: Kostenarten Summen {kostenarten_summen}")
    
    # Gruppiere nach Wirtschaftsplan-Kategorien basierend auf dem Mapping
    kategorien_summen = {}
    
    # Initialisiere alle bekannten Kategorien
    for kategorie in kategorie_mappings.keys():
        kategorien_summen[kategorie] = 0
    
    # Fülle die Summen basierend auf den Mappings
    for kostenart, betrag in kostenarten_summen.items():
        # Finde die zugehörige Kategorie
        kategorie = get_kategorie_for_kostenart(kostenart)
        #print(f"DEBUG: Mapping für Kostenart '{kostenart}': {kategorie}")
        
        if kategorie:
            # Wenn es ein Mapping gibt, addiere zum richtigen Kategorie-Eintrag
            kategorien_summen[kategorie] += betrag
        else:
            # Wenn kein Mapping, unter "Sonstige" erfassen
            if 'Sonstige' not in kategorien_summen:
                kategorien_summen['Sonstige'] = 0
            kategorien_summen['Sonstige'] += betrag
    
    #print(f"DEBUG: Kategorien Summen nach Mapping {kategorien_summen}")
    
    return {
        'summen': {
            'gesamt': summe_gesamt,
            'umlagefaehig': summe_umlagefaehig,
            'nicht_umlagefaehig': summe_nicht_umlagefaehig,
            'einheiten': summe_einheiten,
            'vf': summe_vf,
            'tg': summe_tg
        },
        'kostenarten': kostenarten_summen,
        'kategorien': kategorien_summen
    }
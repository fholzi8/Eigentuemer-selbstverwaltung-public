"""
Service-Funktionen für Abrechnungen
"""

from decimal import Decimal
from models import db, Miteigentuemer, Transaktion, JahresabschlussKontostand

def get_abrechnung_data(jahr):
    """
    Sammelt alle Daten für die Abrechnungsübersicht
    
    Args:
        jahr (int): Abrechnungsjahr
        
    Returns:
        dict: Enthält alle Daten für die Abrechnungsübersicht
    """
    # Miteigentümer
    miteigentuemer = Miteigentuemer.query.all()
    
    # Gesamtkosten im ausgewählten Jahr
    gesamt_einnahmen = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag > 0, 
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    gesamt_ausgaben = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0, 
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    # Summen für verschiedene Verteilungsschlüssel berechnen
    summe_einheiten = sum(m.einheiten for m in miteigentuemer) if miteigentuemer else 1
    summe_vf = sum(m.vf_einheiten for m in miteigentuemer) if miteigentuemer else 1
    summe_tg = sum(m.tg_einheiten for m in miteigentuemer) if miteigentuemer else 1
    
    # Kostenarten
    kostenarten_stats = db.session.query(
        Transaktion.kostenart, 
        db.func.sum(Transaktion.betrag)
    ).filter(
        Transaktion.betrag < 0,
        Transaktion.jahr == jahr
    ).group_by(Transaktion.kostenart).all()
    
    # Kosten nach Verteilungsschlüssel
    kosten_einheiten = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.verteilungsschluessel == 'Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    kosten_vf = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.verteilungsschluessel == 'VF-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    kosten_tg = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.verteilungsschluessel == 'TG-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    # Umlagefähige Kosten nach Verteilungsschlüssel
    umlagefaehig_einheiten = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.verteilungsschluessel == 'Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    umlagefaehig_vf = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.verteilungsschluessel == 'VF-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    umlagefaehig_tg = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.verteilungsschluessel == 'TG-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    # Jahresabschluss-Daten abrufen
    jahresabschluss = JahresabschlussKontostand.query.filter_by(jahr=jahr).first()
    vorjahres_abschluss = JahresabschlussKontostand.query.filter_by(jahr=jahr-1).first()
    
    vorjahres_saldo = Decimal('0')
    kontostand_jahresende = Decimal('0')
    
    if vorjahres_abschluss:
        vorjahres_saldo = vorjahres_abschluss.vorjahres_saldo
        
    if jahresabschluss:
        kontostand_jahresende = jahresabschluss.kontostand

    # Gesamtsummen
    gesamt_umlagefaehig = umlagefaehig_einheiten + umlagefaehig_vf + umlagefaehig_tg
    gesamt_nicht_umlagefaehig = gesamt_ausgaben - gesamt_umlagefaehig
    
    # Abrechnung pro Miteigentümer
    abrechnungen = []
    for m in miteigentuemer:
        # Direkte Einzahlungen
        einzahlungen = db.session.query(db.func.sum(Transaktion.betrag)).filter(
            Transaktion.miteigentuemer_id == m.id,
            Transaktion.betrag > 0,
            Transaktion.jahr == jahr
        ).scalar() or Decimal('0')
        
        # Anteile berechnen
        # 1. Kosten nach Standard-Einheiten (alle zahlen)
        anteil_einheiten = Decimal(str(m.einheiten / summe_einheiten)) * kosten_einheiten
        
        # Guthaben aus dem Vorjahr
        guthaben_vorjahr = Decimal('0')
        if m.guthaben_jahr == jahr - 1:
            guthaben_vorjahr = m.guthaben_vorjahr

        # 2. Kosten nach VF-Einheiten (nur wer VF-Einheiten hat)
        anteil_vf = Decimal('0')
        if m.vf_einheiten > 0 and summe_vf > 0:
            anteil_vf = Decimal(str(m.vf_einheiten / summe_vf)) * kosten_vf
        
        # 3. Kosten nach TG-Einheiten (nur wer TG-Einheiten hat)
        anteil_tg = Decimal('0')
        if m.tg_einheiten > 0 and summe_tg > 0:
            anteil_tg = Decimal(str(m.tg_einheiten / summe_tg)) * kosten_tg
        
        # Gesamtanteil an Kosten
        anteil_gesamt = anteil_einheiten + anteil_vf + anteil_tg
        
        # Umlagefähige Kosten
        anteil_umlagefaehig_einheiten = Decimal(str(m.einheiten / summe_einheiten)) * umlagefaehig_einheiten
        
        anteil_umlagefaehig_vf = Decimal('0')
        if m.vf_einheiten > 0 and summe_vf > 0:
            anteil_umlagefaehig_vf = Decimal(str(m.vf_einheiten / summe_vf)) * umlagefaehig_vf
        
        anteil_umlagefaehig_tg = Decimal('0')
        if m.tg_einheiten > 0 and summe_tg > 0:
            anteil_umlagefaehig_tg = Decimal(str(m.tg_einheiten / summe_tg)) * umlagefaehig_tg
        
        anteil_umlagefaehig = anteil_umlagefaehig_einheiten + anteil_umlagefaehig_vf + anteil_umlagefaehig_tg
        anteil_nicht_umlagefaehig = anteil_gesamt - anteil_umlagefaehig
        
        # Saldo (positiv = Guthaben, negativ = Nachzahlung)
        saldo = einzahlungen + anteil_gesamt + guthaben_vorjahr
        
        abrechnungen.append({
            'miteigentuemer': m,
            'einzahlungen': einzahlungen,
            'anteil_einheiten': anteil_einheiten,
            'anteil_vf': anteil_vf,
            'anteil_tg': anteil_tg,
            'anteil_gesamt': anteil_gesamt,
            'anteil_umlagefaehig': anteil_umlagefaehig,
            'anteil_nicht_umlagefaehig': anteil_nicht_umlagefaehig,
            'guthaben_vorjahr': guthaben_vorjahr,
            'saldo': saldo
        })
    
    return {
        'gesamt_einnahmen': gesamt_einnahmen,
        'gesamt_ausgaben': gesamt_ausgaben,
        'gesamt_umlagefaehig': gesamt_umlagefaehig,
        'gesamt_nicht_umlagefaehig': gesamt_nicht_umlagefaehig,
        'vorjahres_saldo': vorjahres_saldo,
        'kontostand_jahresende': kontostand_jahresende,
        'kostenarten_stats': kostenarten_stats,
        'abrechnungen': abrechnungen,
        'kosten_einheiten': kosten_einheiten,
        'kosten_vf': kosten_vf,
        'kosten_tg': kosten_tg
    }

def generate_abrechnung_detail(miteigentuemer_id, jahr):
    """
    Generiert detaillierte Abrechnungsdaten für einen Miteigentümer
    
    Args:
        miteigentuemer_id (int): ID des Miteigentümers
        jahr (int): Abrechnungsjahr
        
    Returns:
        dict: Enthält detaillierte Abrechnungsdaten oder None bei Fehler
    """
    miteigentuemer = Miteigentuemer.query.get(miteigentuemer_id)
    
    if not miteigentuemer:
        return None
    
    # Alle Miteigentümer für die Berechnung holen
    alle_miteigentuemer = Miteigentuemer.query.all()
    
    # MEA-Anteile berechnen
    gesamt_mea = sum(m.mea for m in alle_miteigentuemer) if alle_miteigentuemer else 1
    anteil_mea = Decimal(str(miteigentuemer.mea / gesamt_mea)) if gesamt_mea > 0 else Decimal('0')
    
    # Summen für verschiedene Verteilungsschlüssel berechnen
    summe_einheiten = sum(m.einheiten for m in alle_miteigentuemer) if alle_miteigentuemer else 1
    summe_vf = sum(m.vf_einheiten for m in alle_miteigentuemer) if alle_miteigentuemer else 1
    summe_tg = sum(m.tg_einheiten for m in alle_miteigentuemer) if alle_miteigentuemer else 1
    
    # Direkte Einzahlungen
    einzahlungen = Transaktion.query.filter(
        Transaktion.miteigentuemer_id == miteigentuemer_id,
        Transaktion.betrag > 0,
        Transaktion.jahr == jahr
    ).order_by(Transaktion.datum).all()
    
    # Kosten nach Verteilungsschlüssel
    kosten_einheiten = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.verteilungsschluessel == 'Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    kosten_vf = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.verteilungsschluessel == 'VF-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    kosten_tg = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.verteilungsschluessel == 'TG-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    # Umlagefähige Kosten nach Verteilungsschlüssel
    umlagefaehig_einheiten = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.verteilungsschluessel == 'Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    umlagefaehig_vf = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.verteilungsschluessel == 'VF-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    umlagefaehig_tg = db.session.query(db.func.sum(Transaktion.betrag)).filter(
        Transaktion.betrag < 0,
        Transaktion.umlagefaehig == True,
        Transaktion.verteilungsschluessel == 'TG-Einheiten',
        Transaktion.jahr == jahr
    ).scalar() or Decimal('0')
    
    # Kostendetails nach Kostenarten und Verteilungsschlüssel
    kosten_details = []
    
    # Alle Transaktionen für die Kostenübersicht holen (ohne Einzahlungen)
    kosten_nach_art_und_schluessel = db.session.query(
        Transaktion.kostenart,
        Transaktion.verteilungsschluessel,
        Transaktion.umlagefaehig,
        db.func.sum(Transaktion.betrag)
    ).filter(
        Transaktion.betrag < 0,
        Transaktion.jahr == jahr
    ).group_by(
        Transaktion.kostenart, 
        Transaktion.verteilungsschluessel, 
        Transaktion.umlagefaehig
    ).all()
    
    # Für jede Kostenart den Anteil des Miteigentümers berechnen
    for kostenart, verteilungsschluessel, umlagefaehig, betrag in kosten_nach_art_und_schluessel:
        # Je nach Verteilungsschlüssel den richtigen Anteil berechnen
        anteil = Decimal('0')
        
        if verteilungsschluessel == 'Einheiten':
            anteil = Decimal(str(miteigentuemer.einheiten / summe_einheiten)) * betrag
        elif verteilungsschluessel == 'VF-Einheiten' and miteigentuemer.vf_einheiten > 0 and summe_vf > 0:
            anteil = Decimal(str(miteigentuemer.vf_einheiten / summe_vf)) * betrag
        elif verteilungsschluessel == 'TG-Einheiten' and miteigentuemer.tg_einheiten > 0 and summe_tg > 0:
            anteil = Decimal(str(miteigentuemer.tg_einheiten / summe_tg)) * betrag
        
        kosten_details.append({
            'kostenart': kostenart,
            'verteilungsschluessel': verteilungsschluessel,
            'umlagefaehig': umlagefaehig,
            'betrag': betrag,
            'anteil': anteil
        })
    
    # Guthaben aus Vorjahr berücksichtigen
    guthaben_vorjahr = Decimal('0')
    if miteigentuemer.guthaben_jahr == jahr - 1:
        guthaben_vorjahr = miteigentuemer.guthaben_vorjahr

    # Anteile berechnen
    # 1. Kosten nach Standard-Einheiten (alle zahlen)
    anteil_einheiten = Decimal(str(miteigentuemer.einheiten / summe_einheiten)) * kosten_einheiten
    
    # 2. Kosten nach VF-Einheiten (nur wer VF-Einheiten hat)
    anteil_vf = Decimal('0')
    if miteigentuemer.vf_einheiten > 0 and summe_vf > 0:
        anteil_vf = Decimal(str(miteigentuemer.vf_einheiten / summe_vf)) * kosten_vf
    
    # 3. Kosten nach TG-Einheiten (nur wer TG-Einheiten hat)
    anteil_tg = Decimal('0')
    if miteigentuemer.tg_einheiten > 0 and summe_tg > 0:
        anteil_tg = Decimal(str(miteigentuemer.tg_einheiten / summe_tg)) * kosten_tg
    
    # Gesamtanteil an Kosten
    anteil_gesamt = anteil_einheiten + anteil_vf + anteil_tg
    
    # Anteile an umlagefähigen Kosten
    anteil_umlagefaehig_einheiten = Decimal(str(miteigentuemer.einheiten / summe_einheiten)) * umlagefaehig_einheiten
    
    anteil_umlagefaehig_vf = Decimal('0')
    if miteigentuemer.vf_einheiten > 0 and summe_vf > 0:
        anteil_umlagefaehig_vf = Decimal(str(miteigentuemer.vf_einheiten / summe_vf)) * umlagefaehig_vf
    
    anteil_umlagefaehig_tg = Decimal('0')
    if miteigentuemer.tg_einheiten > 0 and summe_tg > 0:
        anteil_umlagefaehig_tg = Decimal(str(miteigentuemer.tg_einheiten / summe_tg)) * umlagefaehig_tg
    
    anteil_umlagefaehig = anteil_umlagefaehig_einheiten + anteil_umlagefaehig_vf + anteil_umlagefaehig_tg
    anteil_nicht_umlagefaehig = anteil_gesamt - anteil_umlagefaehig
    
    # Summe der Einzahlungen berechnen
    summe_einzahlungen = sum(e.betrag for e in einzahlungen)
    
    # Saldo berechnen ohne Guthaben
    #saldo = summe_einzahlungen + anteil_gesamt  # anteil_gesamt ist negativ

    # Saldo berechnen (jetzt mit Berücksichtigung des Guthabens aus dem Vorjahr)
    saldo = summe_einzahlungen + anteil_gesamt + guthaben_vorjahr  # anteil_gesamt ist negativ
    
    return {
        'miteigentuemer': miteigentuemer,
        'einzahlungen': einzahlungen,
        'summe_einzahlungen': summe_einzahlungen,
        'anteil_einheiten': anteil_einheiten,
        'anteil_vf': anteil_vf,
        'anteil_tg': anteil_tg,
        'anteil_gesamt': anteil_gesamt,
        'anteil_umlagefaehig': anteil_umlagefaehig,
        'anteil_nicht_umlagefaehig': anteil_nicht_umlagefaehig,
        'guthaben_vorjahr': guthaben_vorjahr,
        'saldo': saldo,
        'kosten_details': kosten_details,
        'anteil_mea': anteil_mea
    }
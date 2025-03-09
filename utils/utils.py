"""
Allgemeine Hilfsfunktionen für die WEG-Abrechnung Anwendung
"""

import pandas as pd
import datetime
import os
from decimal import Decimal
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import decimal
import logging

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename, extensions=None):
    """
    Überprüft, ob der Dateityp erlaubt ist
    
    Args:
        filename (str): Name der Datei
        extensions (list, optional): Liste der erlaubten Dateiendungen. Defaults to None.
    
    Returns:
        bool: True wenn der Dateityp erlaubt ist, sonst False
    """
    if extensions is None:
        # Standard-Extensions
        extensions = ['csv', 'xlsx', 'xls']
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def kategorisiere_transaktion(beschreibung, kategorie, betrag):
    """
    Automatische Kategorisierung von Transaktionen basierend auf Beschreibung und Kategorie
    
    Args:
        beschreibung (str): Beschreibung der Transaktion
        kategorie (str): Kategorie der Transaktion (z.B. vom Banksystem)
        betrag (Decimal): Betrag der Transaktion
    
    Returns:
        tuple: (kostenart, umlagefaehig, verteilungsschluessel)
    """
    kostenart = "Sonstige"
    umlagefaehig = False
    
    # Prüfung aus der Beschreibung
    beschreibung_lower = beschreibung.lower()
    kategorie_lower = kategorie.lower() if kategorie else ""
    
    # Strom ist umlagefähig
    if "strom" in beschreibung_lower or "swm" in kategorie_lower:
        kostenart = "Strom"
        umlagefaehig = True
    # Versicherungen sind umlagefähig
    elif "versicherung" in beschreibung_lower or "versicherungskammer" in kategorie_lower or "haft unf" in beschreibung_lower:
        kostenart = "Versicherung"
        umlagefaehig = True
    # Hausmeister/Minijob ist umlagefähig
    elif "minijob" in beschreibung_lower or "ibrahimovic" in kategorie_lower or "beitrag" in beschreibung_lower or "knappschaft" in kategorie_lower:
        kostenart = "Hausmeister"
        umlagefaehig = True
    # Verwaltungskosten nicht umlagefähig
    elif "matera" in kategorie_lower or "matera" in beschreibung_lower:
        kostenart = "Verwaltung"
        umlagefaehig = False
    # Instandhaltung/Reparaturen teilweise umlagefähig
    elif ("feuerloescher" in beschreibung_lower or 
          "bauunternehmen" in kategorie_lower or 
          "tg-einfahrt" in beschreibung_lower or 
          "thermoflam" in beschreibung_lower):
        kostenart = "Instandhaltung"
        # Kleinere Reparaturen umlagefähig, größere Renovierungen nicht
        umlagefaehig = abs(float(betrag)) < 500
    # Telekommunikation umlagefähig
    elif "vodafone" in kategorie_lower or "vodafone" in beschreibung_lower:
        kostenart = "Telekommunikation"
        umlagefaehig = True
    # Sonderumlage/Rücklage nicht umlagefähig
    elif "rücklagen" in beschreibung_lower or "rücklagen" in kategorie_lower:
        kostenart = "Rücklage"
        umlagefaehig = False
    
    # Einzahlungen als spezielle Kategorie
    if float(betrag) > 0:
        kostenart = "Einzahlung"
    
    # Verteilungsschlüssel bestimmen
    verteilungsschluessel = "Einheiten"  # Default
    if "tg" in beschreibung_lower or "tiefgarage" in beschreibung_lower:
        verteilungsschluessel = "TG-Einheiten"
    elif "gemeinschaftsfläche" in beschreibung_lower or "wohnung" in beschreibung_lower:
        verteilungsschluessel = "VF-Einheiten"
    
    return kostenart, umlagefaehig, verteilungsschluessel

def parse_german_date(date_str):
    """
    Konvertiert deutsches Datum in ein datetime.date-Objekt
    
    Args:
        date_str (str): Datumsstring (z.B. '31.12.2023' oder '2023-12-31')
    
    Returns:
        datetime.date: Konvertiertes Datum
    """
    try:
        # Format: TT.MM.YYYY
        if '.' in date_str:
            parts = date_str.split('.')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                return datetime.date(year, month, day)
        # Format: YYYY-MM-DD
        elif '-' in date_str:
            year, month, day = map(int, date_str.split('-'))
            return datetime.date(year, month, day)
        # Format: DD/MM/YYYY
        elif '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                return datetime.date(year, month, day)
    except ValueError as e:
        logger.error(f"Fehler beim Parsen des Datums {date_str}: {e}")
    
    # Fallback: Aktuelles Datum
    logger.warning(f"Konnte Datum nicht parsen, verwende aktuelles Datum: {date_str}")
    return datetime.date.today()

def importiere_csv(file_path):
    """
    Importiert CSV- oder Excel-Datei mit Banktransaktionen
    
    Args:
        file_path (str): Pfad zur CSV/Excel-Datei
    
    Returns:
        tuple: (list mit Transaktionen, error_message)
    """
    import pandas as pd
    import os
    import re
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)
    
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Manuelles Parsing für ungewöhnliche Formate
        transactions = []
        
        if file_extension in ['.xlsx', '.xls']:
            # Excel-Datei mit spezieller Vorverarbeitung
            try:
                # Zuerst als normales Excel versuchen
                df = pd.read_excel(file_path)
                
                # Prüfen, ob die Excel-Datei ein ungewöhnliches Format hat (eine Spalte mit allem drin)
                if len(df.columns) == 1:
                    # Dateipfad lesen und String-Zeilen extrahieren
                    content_rows = []
                    
                    # Alle Zellen in der ersten (und einzigen) Spalte durchgehen
                    for idx, row in df.iterrows():
                        cell_content = str(row.iloc[0]).strip()
                        if cell_content and not pd.isna(cell_content):
                            content_rows.append(cell_content)
                    
                    # CSV-Format im Inneren einer Excel-Zelle
                    if len(content_rows) > 0:
                        # Prüfen, ob die erste Zeile eine Header-Zeile ist
                        header_match = re.search(r'datum\s*;.*beschreibung.*;\s*betrag', content_rows[0].lower())
                        start_idx = 1 if header_match else 0
                        
                        # Transaktionen parsen
                        for row_idx in range(start_idx, len(content_rows)):
                            row = content_rows[row_idx]
                            # Splitten nach Semikolon, aber nicht innerhalb von Anführungszeichen
                            parts = [part.strip() for part in row.split(';')]
                            
                            if len(parts) >= 3:
                                datum_str = parts[0].strip()
                                beschreibung = parts[1].strip()
                                betrag_str = parts[2].strip().replace(',', '.')
                                
                                # Datum parsen
                                datum = parse_german_date(datum_str)
                                
                                try:
                                    betrag = float(betrag_str)
                                    
                                    # Kategorisieren
                                    kostenart, umlagefaehig, verteilungsschluessel = kategorisiere_transaktion(
                                        beschreibung, "", betrag
                                    )
                                    
                                    transactions.append({
                                        'datum': datum,
                                        'beschreibung': beschreibung,
                                        'kategorie': "",
                                        'kostenart': kostenart,
                                        'betrag': betrag,
                                        'umlagefaehig': umlagefaehig,
                                        'verteilungsschluessel': verteilungsschluessel,
                                        'jahr': datum.year
                                    })
                                except ValueError:
                                    logger.warning(f"Konnte Betrag nicht parsen: {betrag_str}")
                    
                    if transactions:
                        return transactions, None
            except Exception as e:
                logger.warning(f"Konnte Excel-Datei nicht als eine Spalte lesen: {e}")
                
            # Falls obige Methode fehlschlägt, versuchen wir es mit normalem Excel
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                # Prüfen, ob die erforderlichen Spalten vorhanden sind
                has_datum = any('datum' in col.lower() for col in df.columns)
                has_betrag = any('betrag' in col.lower() for col in df.columns)
                
                if has_datum and has_betrag:
                    # Normale Excel-Verarbeitung
                    pass  # Wird unten im Standardcode behandelt
                else:
                    # Versuchen wir es mit einer anderen Methode, vielleicht ist es ein CSV-in-Excel Format
                    with open(file_path, 'rb') as f:
                        raw_data = f.read()
                    
                    # Konvertieren zu Text
                    try:
                        from io import StringIO
                        import chardet
                        
                        encoding = chardet.detect(raw_data)['encoding']
                        text_data = raw_data.decode(encoding or 'utf-8')
                        
                        # Zeilenumbrüche normalisieren
                        text_data = text_data.replace('\r\n', '\n').replace('\r', '\n')
                        
                        # Wieder in eine StringIO umwandeln
                        data_io = StringIO(text_data)
                        
                        # Als CSV lesen
                        df = pd.read_csv(data_io, sep=';')
                        
                        # Standardverarbeitung wird unten fortgesetzt
                    except Exception as e2:
                        logger.error(f"Fehler beim Konvertieren von Excel zu Text: {e2}")
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Excel-Datei: {e}")
                return None, f"Fehler beim Lesen der Excel-Datei: {str(e)}"
        else:
            # Für CSV-Dateien: Erst als Text lesen
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Falls UTF-8 fehlschlägt, versuchen wir andere Encodings
                try:
                    with open(file_path, 'r', encoding='latin1') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"Fehler beim Lesen der CSV-Datei mit latin1 Encoding: {e}")
                    return None, f"Fehler beim Lesen der Datei: {str(e)}"
            
            # Zuerst als Text parsen - Zeilenumbrüche normalisieren
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            lines = content.split('\n')
            
            # Prüfen, ob es sich um ein CSV-in-einer-Spalte Format handelt
            if len(lines) > 1:
                # Prüfen, ob die erste Zeile eine Header-Zeile ist
                header_match = re.search(r'datum\s*;.*beschreibung.*;\s*betrag', lines[0].lower())
                start_idx = 1 if header_match else 0
                
                # Manuelles Parsen
                for i in range(start_idx, len(lines)):
                    line = lines[i].strip()
                    if not line:
                        continue
                    
                    # Zeilen mit Semikolon-Feldern
                    parts = [part.strip() for part in line.split(';')]
                    if len(parts) >= 3:
                        datum_str = parts[0].strip()
                        beschreibung = parts[1].strip()
                        betrag_str = parts[2].strip().replace(',', '.')
                        
                        # Datum parsen
                        datum = parse_german_date(datum_str)
                        
                        try:
                            betrag = float(betrag_str)
                            
                            # Kategorisieren
                            kostenart, umlagefaehig, verteilungsschluessel = kategorisiere_transaktion(
                                beschreibung, "", betrag
                            )
                            
                            transactions.append({
                                'datum': datum,
                                'beschreibung': beschreibung,
                                'kategorie': "",
                                'kostenart': kostenart,
                                'betrag': betrag,
                                'umlagefaehig': umlagefaehig,
                                'verteilungsschluessel': verteilungsschluessel,
                                'jahr': datum.year
                            })
                        except ValueError:
                            logger.warning(f"Konnte Betrag nicht parsen: {betrag_str}")
            
            if transactions:
                return transactions, None
            
            # Wenn manuelles Parsen fehlschlägt, versuchen wir die Standard-Methode mit pandas
            try:
                df = pd.read_csv(file_path, sep=';', encoding='utf-8', decimal=',')
            except Exception as e1:
                try:
                    df = pd.read_csv(file_path, sep=',', encoding='utf-8')
                except Exception as e2:
                    try:
                        df = pd.read_csv(file_path, sep=';', encoding='latin1', decimal=',')
                    except Exception as e3:
                        logger.error(f"Alle CSV-Parsing-Methoden fehlgeschlagen: {e1}, {e2}, {e3}")
                        # Wenn wir Transaktionen manuell geparst haben, nutzen wir diese
                        if transactions:
                            return transactions, None
                        return None, f"Fehler beim Lesen der CSV-Datei. Bitte prüfen Sie das Format."
        
        # Falls wir hier sind, haben wir ein DataFrame, das wir normalisieren können
        # Spalten standardisieren
        standard_columns = {
            'datum': ['datum', 'date', 'buchungstag', 'valuta', 'wertstellung'],
            'beschreibung': ['beschreibung', 'verwendungszweck', 'text', 'buchungstext'],
            'kategorie': ['kategorie', 'category', 'buchungsgruppe'],
            'betrag': ['betrag', 'amount', 'wert', 'umsatz']
        }
        
        # Spalten normalisieren - Leerzeichen entfernen und kleinschreiben
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Spalten-Mapping erstellen
        column_mapping = {}
        for target, source_options in standard_columns.items():
            for source in source_options:
                matching_cols = [col for col in df.columns if source in col.lower()]
                if matching_cols:
                    column_mapping[matching_cols[0]] = target
                    break
        
        # Spalten umbenennen
        df = df.rename(columns=column_mapping)
        
        # Stellen sicher, dass die erforderlichen Spalten vorhanden sind
        required_columns = ['datum', 'beschreibung', 'betrag']
        for col in required_columns:
            if col not in df.columns:
                # Wenn wir Transaktionen manuell geparst haben, nutzen wir diese
                if transactions:
                    return transactions, None
                return None, f"Die Spalte '{col}' fehlt in der Datei"
        
        # Kategorie-Spalte hinzufügen, falls nicht vorhanden
        if 'kategorie' not in df.columns:
            df['kategorie'] = ""
        
        # Datum konvertieren
        df['datum'] = df['datum'].apply(lambda x: parse_german_date(str(x)))
        
        # Betrag als Dezimalzahl konvertieren
        if df['betrag'].dtype == object:
            df['betrag'] = df['betrag'].str.replace('.', '').str.replace(',', '.').astype(float)
        
        # Kategorisieren und Jahr hinzufügen
        for _, row in df.iterrows():
            kostenart, umlagefaehig, verteilungsschluessel = kategorisiere_transaktion(
                row['beschreibung'], row['kategorie'], row['betrag']
            )
            transactions.append({
                'datum': row['datum'],
                'beschreibung': row['beschreibung'],
                'kategorie': row['kategorie'],
                'kostenart': kostenart,
                'betrag': row['betrag'],
                'umlagefaehig': umlagefaehig,
                'verteilungsschluessel': verteilungsschluessel,
                'jahr': row['datum'].year
            })
        
        return transactions, None
    except Exception as e:
        logger.error(f"Fehler beim Importieren der Datei: {e}", exc_info=True)
        return None, f"Unerwarteter Fehler beim Importieren: {str(e)}"

def erstelle_abrechnung_pdf(miteigentuemer, jahr, einzahlungen, kosten_details, anteil_mea, 
                            anteil_umlagefaehig, anteil_nicht_umlagefaehig, anteil_gesamt, saldo):
    """
    Erstellt ein PDF mit der Abrechnung für einen Miteigentümer
    
    Args:
        miteigentuemer: Miteigentümer-Objekt
        jahr: Abrechnungsjahr
        einzahlungen: Liste der Einzahlungen
        kosten_details: Liste mit Kostendetails
        anteil_mea: MEA-Anteil des Miteigentümers
        anteil_umlagefaehig: Anteil an umlagefähigen Kosten
        anteil_nicht_umlagefaehig: Anteil an nicht umlagefähigen Kosten
        anteil_gesamt: Gesamtanteil an Kosten
        saldo: Saldo (positiv = Guthaben, negativ = Nachzahlung)
    
    Returns:
        BytesIO: PDF-Dokument als BytesIO-Objekt
    """
    # PDF im Speicher erstellen (kein Dateischreiben)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.topMargin = 2 * cm
    doc.bottomMargin = 2 * cm
    doc.leftMargin = 2 * cm
    doc.rightMargin = 2 * cm
    
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold'
    )
    
    elements = []
    
    # Titel
    titel_stil = ParagraphStyle(
        'TitelStil',
        parent=styles['Heading1'],
        alignment=1,  # Zentriert
        spaceAfter=0.5*cm
    )
    elements.append(Paragraph(f"Jahresabrechnung {jahr}", titel_stil))
    elements.append(Paragraph(f"WEG Friedrichshafener Straße 37-63", styles['Heading3']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Miteigentümer-Infos
    elements.append(Paragraph(f"<b>Miteigentümer:</b> {miteigentuemer.name}", styles['Normal']))
    elements.append(Paragraph(f"<b>MEA-Anteile:</b> {miteigentuemer.mea} ({anteil_mea*100:.2f}%)", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Berechnen der Summe der Einzahlungen vorab
    summe_einzahlungen = sum(e.betrag for e in einzahlungen)
    
    # Einzahlungen Tabelle
    if einzahlungen:
        elements.append(Paragraph("<b>Einzahlungen:</b>", styles['Heading3']))
        einzahlungen_daten = [['Datum', 'Beschreibung', 'Betrag (€)']]
        
        for e in einzahlungen:
            einzahlungen_daten.append([
                e.datum.strftime('%d.%m.%Y'),
                e.beschreibung,
                f"{e.betrag:.2f}".replace('.', ',')
            ])
            
        einzahlungen_daten.append(['', 'Summe Einzahlungen', f"{summe_einzahlungen:.2f}".replace('.', ',')])
        
        einzahlungen_tabelle = Table(einzahlungen_daten, colWidths=[2.5*cm, 9*cm, 3*cm])
        einzahlungen_tabelle.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -2), 0.25, colors.black),
            ('BOX', (0, -1), (-1, -1), 0.25, colors.black),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Fette Schrift für die Summenzeile
        ]))
        elements.append(einzahlungen_tabelle)
        elements.append(Spacer(1, 0.5*cm))
    
    # Kosten Tabelle
    elements.append(Paragraph("<b>Kostenübersicht:</b>", styles['Heading3']))
    kosten_daten = [['Kostenart', 'Verteilungsschlüssel', 'Umlagefähig', 'Gesamtbetrag (€)', 'Ihr Anteil (€)']]
    
    umlagefaehig_summe = decimal.Decimal('0.00')
    nicht_umlagefaehig_summe = decimal.Decimal('0.00')
    
    # Nur relevante Kosten anzeigen (basierend auf Verteilungsschlüsseln)
    relevante_kosten = []
    for k in kosten_details:
        if (k['verteilungsschluessel'] == 'Einheiten' and miteigentuemer.einheiten > 0 or
            k['verteilungsschluessel'] == 'VF-Einheiten' and miteigentuemer.vf_einheiten > 0 or
            k['verteilungsschluessel'] == 'TG-Einheiten' and miteigentuemer.tg_einheiten > 0):
            relevante_kosten.append(k)
    
    for k in relevante_kosten:
        kosten_daten.append([
            k['kostenart'],
            k['verteilungsschluessel'],
            'Ja' if k['umlagefaehig'] else 'Nein',
            f"{k['betrag']:.2f}".replace('.', ','),
            f"{k['anteil']:.2f}".replace('.', ',')
        ])
        
        if k['umlagefaehig']:
            umlagefaehig_summe += k['anteil']
        else:
            nicht_umlagefaehig_summe += k['anteil']
    
    # Füge die Summenzeilen mit korrekter Formatierung hinzu
    kosten_daten.append(['Umlagefähige Kosten', '', '', '', f"{anteil_umlagefaehig:.2f}".replace('.', ',')])
    kosten_daten.append(['Nicht umlagefähige Kosten', '', '', '', f"{anteil_nicht_umlagefaehig:.2f}".replace('.', ',')])
    kosten_daten.append(['Gesamtkosten', '', '', '', f"{anteil_gesamt:.2f}".replace('.', ',')])
    
    kosten_tabelle = Table(kosten_daten, colWidths=[3.5*cm, 3*cm, 2.5*cm, 3*cm, 3*cm])
    kosten_tabelle.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -4), 0.25, colors.black),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),  # Fette Schrift für die letzten drei Zeilen
    ]))
    elements.append(kosten_tabelle)
    elements.append(Spacer(1, 1*cm))
    
    # Abrechnung Zusammenfassung
    elements.append(Paragraph("<b>Abrechnung:</b>", styles['Heading3']))
    abrechnung_daten = [
        ['Einzahlungen:', f"{summe_einzahlungen:.2f} €".replace('.', ',')],
        ['abzüglich Gesamtanteil:', f"{anteil_gesamt:.2f} €".replace('.', ',')],
        ['Saldo:', f"{saldo:.2f} €".replace('.', ',')]
    ]
    
    abrechnung_tabelle = Table(abrechnung_daten, colWidths=[5*cm, 3*cm])
    abrechnung_tabelle.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Fett für die Saldo-Zeile
    ]))
    elements.append(abrechnung_tabelle)
    elements.append(Spacer(1, 0.5*cm))
    
    # Hinweis zu Saldo
    if saldo < 0:
        elements.append(Paragraph(f"<b>Hinweis:</b> Es besteht eine Nachzahlungspflicht in Höhe von {abs(saldo):.2f} €.".replace('.', ','), styles['Normal']))
    elif saldo > 0:
        elements.append(Paragraph(f"<b>Hinweis:</b> Es besteht ein Guthaben in Höhe von {saldo:.2f} €.".replace('.', ','), styles['Normal']))
    else:
        elements.append(Paragraph("<b>Hinweis:</b> Die Abrechnung ist ausgeglichen.", styles['Normal']))
    
    # PDF erstellen
    doc.build(elements)
    buffer.seek(0)
    return buffer

def check_upload_dir(upload_dir):
    """
    Überprüft, ob das Upload-Verzeichnis existiert und erstellt es, falls nötig
    
    Args:
        upload_dir (str): Pfad zum Upload-Verzeichnis
    """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload-Verzeichnis erstellt: {upload_dir}")
    
    # Prüfen, ob es beschreibbar ist
    if not os.access(upload_dir, os.W_OK):
        logger.warning(f"Upload-Verzeichnis ist nicht beschreibbar: {upload_dir}")
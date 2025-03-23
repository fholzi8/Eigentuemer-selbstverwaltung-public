"""
Exportfunktionen für die WEG-App
"""

import csv
import io
import pandas as pd
from flask import Response
from decimal import Decimal

def export_transaktionen_as_csv(transaktionen, year=None):
    """
    Exportiert Transaktionen als CSV-Datei
    
    Args:
        transaktionen: Liste von Transaktion-Objekten oder Query
        year: Optional, das Jahr für den Dateinamen
    
    Returns:
        Response: Flask-Response mit CSV-Datei zum Download
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Header
    writer.writerow(['Datum', 'Beschreibung', 'Kategorie', 'Kostenart', 'Betrag', 'Umlagefähig', 
                     'Verteilungsschlüssel', 'Miteigentümer', 'Jahr'])
    
    # Daten
    for t in transaktionen:
        writer.writerow([
            t.datum.strftime('%d.%m.%Y'),
            t.beschreibung,
            t.kategorie,
            t.kostenart,
            str(t.betrag).replace('.', ','),
            'Ja' if t.umlagefaehig else 'Nein',
            t.verteilungsschluessel,
            t.miteigentuemer.name if t.miteigentuemer else '',
            t.jahr
        ])
    
    output.seek(0)
    
    year_string = f"_{year}" if year else ""
    filename = f"transaktionen{year_string}.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

def export_transaktionen_as_excel(transaktionen, year=None):
    """
    Exportiert Transaktionen als Excel-Datei
    
    Args:
        transaktionen: Liste von Transaktion-Objekten oder Query
        year: Optional, das Jahr für den Dateinamen
    
    Returns:
        Response: Flask-Response mit Excel-Datei zum Download
    """
    # Daten für Excel vorbereiten
    data = []
    for t in transaktionen:
        data.append({
            'Datum': t.datum,
            'Beschreibung': t.beschreibung,
            'Kategorie': t.kategorie,
            'Kostenart': t.kostenart,
            'Betrag': t.betrag,
            'Umlagefähig': 'Ja' if t.umlagefaehig else 'Nein',
            'Verteilungsschlüssel': t.verteilungsschluessel,
            'Miteigentümer': t.miteigentuemer.name if t.miteigentuemer else '',
            'Jahr': t.jahr
        })
    
    # DataFrame erstellen
    df = pd.DataFrame(data)
    
    # In Excel-Bytes konvertieren
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaktionen')
        
        # Formatierung
        workbook = writer.book
        worksheet = writer.sheets['Transaktionen']
        
        # Datumsformat
        date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})
        worksheet.set_column('A:A', 12, date_format)
        
        # Text-Spalten
        worksheet.set_column('B:B', 50)  # Beschreibung
        worksheet.set_column('C:D', 20)  # Kategorie, Kostenart
        
        # Währungsformat
        currency_format = workbook.add_format({'num_format': '#,##0.00 €'})
        worksheet.set_column('E:E', 12, currency_format)
        
        # Andere Spalten
        worksheet.set_column('F:I', 15)
    
    output.seek(0)
    
    year_string = f"_{year}" if year else ""
    filename = f"transaktionen{year_string}.xlsx"
    
    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

def export_kontostaende_as_csv(kontostaende):
    """
    Exportiert Kontostände als CSV-Datei
    
    Args:
        kontostaende: Liste von Kontostand-Objekten oder Query
    
    Returns:
        Response: Flask-Response mit CSV-Datei zum Download
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Header
    writer.writerow(['Datum', 'Betrag', 'Kommentar', 'Erfasst von', 'Erfasst am'])
    
    # Daten
    for k in kontostaende:
        writer.writerow([
            k.datum.strftime('%d.%m.%Y'),
            str(k.betrag).replace('.', ','),
            k.kommentar or '',
            k.user.username if k.user else 'System',
            k.created_at.strftime('%d.%m.%Y %H:%M')
        ])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=kontostaende.csv"}
    )
def export_wirtschaftsplan_as_csv(wirtschaftsplan_eintraege, year=None):
    """
    Exportiert Wirtschaftsplan-Einträge als CSV-Datei
    
    Args:
        wirtschaftsplan_eintraege: Liste von Wirtschaftsplan-Objekten oder Query
        year: Optional, das Jahr für den Dateinamen
    
    Returns:
        Response: Flask-Response mit CSV-Datei zum Download
    """
    import csv
    import io
    from flask import Response
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Header
    writer.writerow(['Jahr', 'Bezeichnung', 'Kategorie', 'Betrag', 'Verteilungsschlüssel', 
                     'Umlagefähig', 'Notiz'])
    
    # Daten
    for wp in wirtschaftsplan_eintraege:
        writer.writerow([
            wp.jahr,
            wp.bezeichnung,
            wp.kategorie or '',
            str(wp.betrag).replace('.', ','),
            wp.verteilungsschluessel,
            'Ja' if wp.umlagefaehig else 'Nein',
            wp.notiz or ''
        ])
    
    output.seek(0)
    
    year_string = f"_{year}" if year else ""
    filename = f"wirtschaftsplan{year_string}.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

def export_wirtschaftsplan_as_excel(wirtschaftsplan_eintraege, year=None):
    """
    Exportiert Wirtschaftsplan-Einträge als Excel-Datei
    
    Args:
        wirtschaftsplan_eintraege: Liste von Wirtschaftsplan-Objekten oder Query
        year: Optional, das Jahr für den Dateinamen
    
    Returns:
        Response: Flask-Response mit Excel-Datei zum Download
    """
    import xlsxwriter
    from io import BytesIO
    from flask import Response
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Wirtschaftsplan')
    
    # Formatierungen
    header_format = workbook.add_format({'bold': True, 'bg_color': '#DDDDDD'})
    currency_format = workbook.add_format({'num_format': '#,##0.00 €'})
    
    # Header
    headers = ['Jahr', 'Bezeichnung', 'Kategorie', 'Betrag', 'Verteilungsschlüssel', 
               'Umlagefähig', 'Notiz']
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Spaltenbreiten
    worksheet.set_column('A:A', 8)   # Jahr
    worksheet.set_column('B:B', 50)  # Bezeichnung
    worksheet.set_column('C:C', 20)  # Kategorie
    worksheet.set_column('D:D', 12)  # Betrag
    worksheet.set_column('E:E', 20)  # Verteilungsschlüssel
    worksheet.set_column('F:F', 15)  # Umlagefähig
    worksheet.set_column('G:G', 40)  # Notiz
    
    # Daten
    for row, wp in enumerate(wirtschaftsplan_eintraege, start=1):
        worksheet.write_number(row, 0, wp.jahr)
        worksheet.write(row, 1, wp.bezeichnung)
        worksheet.write(row, 2, wp.kategorie or '')
        worksheet.write_number(row, 3, float(wp.betrag), currency_format)
        worksheet.write(row, 4, wp.verteilungsschluessel)
        worksheet.write(row, 5, 'Ja' if wp.umlagefaehig else 'Nein')
        worksheet.write(row, 6, wp.notiz or '')
    
    workbook.close()
    output.seek(0)
    
    year_string = f"_{year}" if year else ""
    filename = f"wirtschaftsplan{year_string}.xlsx"
    
    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

def export_abrechnung_as_csv(abrechnungen, jahr):
    """
    Exportiert Abrechnungen pro Miteigentümer als CSV-Datei
    
    Args:
        abrechnungen: Liste von Abrechnungs-Dictionaries
        jahr: Das Jahr der Abrechnung
    
    Returns:
        Response: Flask-Response mit CSV-Datei zum Download
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Header
    header = ['Name', 'MEA', 'Einheiten', 'VF-Einheiten', 'TG-Einheiten', 
             'Einzahlungen', 'Anteil Einheiten', 'Anteil VF', 'Anteil TG', 
             'Anteil Gesamt', 'Anteil umlagefähig', 'Anteil nicht umlagefähig']
    
    # Prüfen, ob Guthaben Vorjahr in den Daten vorhanden ist
    if any('guthaben_vorjahr' in abr for abr in abrechnungen):
        header.append('Guthaben Vorjahr')
    
    header.append('Saldo')
    writer.writerow(header)
    
    # Daten
    for abr in abrechnungen:
        miteigentuemer = abr['miteigentuemer']
        row = [
            miteigentuemer.name,
            miteigentuemer.mea,
            miteigentuemer.einheiten,
            miteigentuemer.vf_einheiten,
            miteigentuemer.tg_einheiten,
            str(abr['einzahlungen']).replace('.', ','),
            str(abr['anteil_einheiten']).replace('.', ','),
            str(abr['anteil_vf']).replace('.', ','),
            str(abr['anteil_tg']).replace('.', ','),
            str(abr['anteil_gesamt']).replace('.', ','),
            str(abr['anteil_umlagefaehig']).replace('.', ','),
            str(abr['anteil_nicht_umlagefaehig']).replace('.', ',')
        ]
        
        # Guthaben Vorjahr hinzufügen, falls vorhanden
        if 'guthaben_vorjahr' in abr:
            row.append(str(abr['guthaben_vorjahr']).replace('.', ','))
        
        row.append(str(abr['saldo']).replace('.', ','))
        writer.writerow(row)
    
    output.seek(0)
    
    filename = f"abrechnung_miteigentuemer_{jahr}.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

def export_abrechnung_as_excel(abrechnungen, jahr):
    """
    Exportiert Abrechnungen pro Miteigentümer als Excel-Datei
    
    Args:
        abrechnungen: Liste von Abrechnungs-Dictionaries
        jahr: Das Jahr der Abrechnung
    
    Returns:
        Response: Flask-Response mit Excel-Datei zum Download
    """
    import xlsxwriter
    from io import BytesIO
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Abrechnung')
    
    # Formatierungen
    header_format = workbook.add_format({'bold': True, 'bg_color': '#DDDDDD'})
    currency_format = workbook.add_format({'num_format': '#,##0.00 €'})
    number_format = workbook.add_format({'num_format': '0'})
    
    # Header
    header = ['Name', 'MEA', 'Einheiten', 'VF-Einheiten', 'TG-Einheiten', 
             'Einzahlungen', 'Anteil Einheiten', 'Anteil VF', 'Anteil TG', 
             'Anteil Gesamt', 'Anteil umlagefähig', 'Anteil nicht umlagefähig']
    
    # Prüfen, ob Guthaben Vorjahr in den Daten vorhanden ist
    has_guthaben_vorjahr = any('guthaben_vorjahr' in abr for abr in abrechnungen)
    if has_guthaben_vorjahr:
        header.append('Guthaben Vorjahr')
    
    header.append('Saldo')
    
    for col, title in enumerate(header):
        worksheet.write(0, col, title, header_format)
    
    # Spaltenbreiten
    worksheet.set_column('A:A', 30)  # Name
    worksheet.set_column('B:E', 12)  # MEA, Einheiten, etc.
    worksheet.set_column('F:M', 18)  # Finanzwerte
    
    # Daten
    for row, abr in enumerate(abrechnungen, start=1):
        miteigentuemer = abr['miteigentuemer']
        
        worksheet.write(row, 0, miteigentuemer.name)
        worksheet.write_number(row, 1, miteigentuemer.mea, number_format)
        worksheet.write_number(row, 2, miteigentuemer.einheiten, number_format)
        worksheet.write_number(row, 3, miteigentuemer.vf_einheiten, number_format)
        worksheet.write_number(row, 4, miteigentuemer.tg_einheiten, number_format)
        
        # Finanzwerte
        col = 5
        for key in ['einzahlungen', 'anteil_einheiten', 'anteil_vf', 'anteil_tg', 
                   'anteil_gesamt', 'anteil_umlagefaehig', 'anteil_nicht_umlagefaehig']:
            worksheet.write_number(row, col, float(abr[key]), currency_format)
            col += 1
        
        # Guthaben Vorjahr, falls vorhanden
        if has_guthaben_vorjahr:
            value = float(abr.get('guthaben_vorjahr', 0))
            worksheet.write_number(row, col, value, currency_format)
            col += 1
        
        # Saldo
        worksheet.write_number(row, col, float(abr['saldo']), currency_format)
    
    workbook.close()
    output.seek(0)
    
    filename = f"abrechnung_miteigentuemer_{jahr}.xlsx"
    
    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

def export_miteigentuemer_as_csv(miteigentuemer_list=None):
    """
    Exportiert Miteigentümer als CSV-Datei
    
    Args:
        miteigentuemer_list (list, optional): Liste der zu exportierenden Miteigentümer
        
    Returns:
        Response: Flask-Response mit CSV-Datei
    """
    from io import StringIO
    import csv
    from datetime import datetime
    from flask import Response, current_app
    
    if miteigentuemer_list is None:
        from models import Miteigentuemer
        miteigentuemer_list = Miteigentuemer.query.all()
    
    # CSV erstellen
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    
    # Spaltenüberschriften
    headers = [
        'ID', 'Name', 'MEA', 'VF-Einheiten', 'TG-Einheiten', 'Einheiten', 
        'Guthaben', 'Guthaben-Jahr', 'Straße', 'PLZ', 'Ort', 'Telefon', 'E-Mail',
        'Kontoinhaber', 'IBAN', 'BIC', 'Bank'
    ]
    csv_writer.writerow(headers)
    
    # Daten schreiben
    for m in miteigentuemer_list:
        row = [
            m.id, m.name, m.mea, m.vf_einheiten, m.tg_einheiten, m.einheiten,
            m.guthaben_vorjahr, m.guthaben_jahr, m.strasse, m.plz, m.ort, m.telefon, m.email,
            m.kontoinhaber, m.iban, m.bic, m.bank_name
        ]
        csv_writer.writerow(row)
    
    # Response erstellen
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"miteigentuemer_export_{timestamp}.csv"
    
    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )
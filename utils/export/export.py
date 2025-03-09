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
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import csv
import sys
from datetime import datetime

def parse_transactions(file_path):
    """
    Parst Banktransaktionen aus einer Textdatei und wandelt sie in strukturierte Daten um.
    """
    transactions = []
    current_month = None
    current_year = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Überprüfen, ob die Zeile mit einer Zahl beginnt (Tag der Transaktion)
        if re.match(r'^\d+\t', line):
            parts = line.split('\t')
            if len(parts) >= 4:
                day = parts[0]
                description = parts[1]
                category = parts[2]
                amount = parts[3]
                
                # Überprüfen, ob die nächste Zeile Monat und Jahr enthält
                if i+1 < len(lines) and re.match(r'^(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\s+\d+$', lines[i+1].strip()):
                    date_parts = lines[i+1].strip().split()
                    current_month = date_parts[0]
                    current_year = date_parts[1]
                
                if current_month and current_year:
                    # Konvertieren des Monatsnamens in eine Zahl
                    month_map = {
                        'Jan': '01', 'Feb': '02', 'Mär': '03', 'Apr': '04',
                        'Mai': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                        'Sep': '09', 'Okt': '10', 'Nov': '11', 'Dez': '12'
                    }
                    month_num = month_map.get(current_month, '01')
                    
                    # Formatieren des Datums
                    date_str = f"{day.zfill(2)}.{month_num}.{current_year}"
                    
                    # Bereinigen des Betrags
                    amount = amount.replace('\u00a0', ' ').strip()
                    
                    transactions.append({
                        'Datum': date_str,
                        'Beschreibung': description,
                        'Kategorie': category,
                        'Betrag': amount
                    })
        i += 1
    
    return transactions

def write_to_csv(transactions, output_file):
    """
    Schreibt die Transaktionen in eine CSV-Datei.
    """
    fieldnames = ['Datum', 'Beschreibung', 'Kategorie', 'Betrag']
    
    with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"CSV-Datei wurde erfolgreich erstellt: {output_file}")
    print(f"Es wurden {len(transactions)} Transaktionen geschrieben.")

def main():
    """
    Hauptfunktion zum Ausführen des Skripts.
    """
    if len(sys.argv) < 2:
        print("Verwendung: python bankdaten_zu_csv.py <eingabedatei> [ausgabedatei]")
        print("Beispiel: python bankdaten_zu_csv.py bank_data.txt bank_transactions.csv")
        return
    
    input_file = sys.argv[1]
    
    # Standard-Ausgabedatei, falls keine angegeben wurde
    output_file = "bank_transactions.csv"
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    
    try:
        transactions = parse_transactions(input_file)
        if transactions:
            write_to_csv(transactions, output_file)
        else:
            print("Keine Transaktionen gefunden.")
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()

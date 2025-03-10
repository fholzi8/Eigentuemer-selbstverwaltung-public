"""
Skript zum Korrigieren von NULL-Werten für guthaben_vorjahr bei Miteigentümern
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Pfad zum Projektverzeichnis hinzufügen, um die Module zu finden
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Eigene Module importieren
from app import app, db
from models import Miteigentuemer

def fix_null_guthaben_values():
    """
    Korrigiert NULL-Werte im Feld guthaben_vorjahr und setzt
    guthaben_jahr auf das Vorjahr, wenn es NULL ist.
    """
    # Aktuelles Jahr und Vorjahr ermitteln
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    with app.app_context():
        # Alle Miteigentümer abrufen
        miteigentuemer_list = Miteigentuemer.query.all()
        
        updated_count = 0
        
        for m in miteigentuemer_list:
            updated = False
            
            # Falls guthaben_vorjahr NULL ist, auf 0 setzen
            if m.guthaben_vorjahr is None:
                m.guthaben_vorjahr = Decimal('0.00')
                updated = True
                print(f"[INFO] Bei Miteigentümer '{m.name}' wurde guthaben_vorjahr auf 0.00 € gesetzt")
            
            # Falls guthaben_jahr NULL ist, auf Vorjahr setzen
            if m.guthaben_jahr is None:
                m.guthaben_jahr = previous_year
                updated = True
                print(f"[INFO] Bei Miteigentümer '{m.name}' wurde guthaben_jahr auf {previous_year} gesetzt")
            
            if updated:
                updated_count += 1
        
        # Nur commit, wenn tatsächlich Änderungen vorgenommen wurden
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"[ERFOLG] {updated_count} Miteigentümer wurden aktualisiert")
            except Exception as e:
                db.session.rollback()
                print(f"[FEHLER] Aktualisierung fehlgeschlagen: {str(e)}")
        else:
            print("[INFO] Keine Miteigentümer mit NULL-Werten gefunden")

if __name__ == "__main__":
    print("Starte Korrektur von NULL-Werten für guthaben_vorjahr...")
    fix_null_guthaben_values()
    print("Fertig!")
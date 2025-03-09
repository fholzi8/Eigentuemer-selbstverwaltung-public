"""
Skript zum Initialisieren der Standard-Kategorie-Kostenart-Mappings
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, KategorieKostenartMapping

def init_mappings():
    """
    Erstellt die Standard-Mappings zwischen Wirtschaftsplan-Kategorien und Transaktions-Kostenarten
    """
    # Standard-Mappings
    mappings = [
        # Betriebskosten
        ('Betriebskosten', 'Hausmeister'),
        ('Betriebskosten', 'Telekommunikation'),
        ('Betriebskosten', 'Strom'),
        
        # Direkte 1:1 Mappings
        ('Instandhaltung', 'Instandhaltung'),
        ('Versicherung', 'Versicherung'),
        ('Verwaltung', 'Verwaltung'),
        
        # Rücklagen (optional)
        ('Rücklagen', 'Einzahlung')
    ]
    
    # Prüfen, ob schon Mappings existieren
    existing_count = KategorieKostenartMapping.query.count()
    if existing_count > 0:
        print(f"Es existieren bereits {existing_count} Mappings. Initialisierung wird übersprungen.")
        return
    
    # Neue Mappings erstellen
    for wp_kategorie, tx_kostenart in mappings:
        mapping = KategorieKostenartMapping(
            wp_kategorie=wp_kategorie,
            tx_kostenart=tx_kostenart
        )
        db.session.add(mapping)
    
    # Änderungen speichern
    db.session.commit()
    print("Standard-Mappings wurden erfolgreich initialisiert.")

if __name__ == '__main__':
    with app.app_context():
        init_mappings()
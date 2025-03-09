"""
Skript zum Erstellen der KategorieKostenartMapping-Tabelle und Initialisieren der Standard-Mappings
"""

from app import app
from models import db, KategorieKostenartMapping

def setup_mappings():
    """
    Erstellt die KategorieKostenartMapping-Tabelle und fügt Standard-Mappings hinzu
    """
    with app.app_context():
        # Prüfen, ob die Tabelle bereits existiert
        table_exists = db.engine.has_table(KategorieKostenartMapping.__tablename__)
        
        if not table_exists:
            # Tabelle erstellen
            print("Erstelle KategorieKostenartMapping-Tabelle...")
            db.create_all()
            print("Tabelle erfolgreich erstellt!")
        
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
    setup_mappings()
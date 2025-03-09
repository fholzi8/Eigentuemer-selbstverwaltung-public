# manual-scripts/init_roadmap.py

import sys
import os
from pathlib import Path

# Pfad zum Projektverzeichnis hinzufügen
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app import app
from models import db, RoadmapItem

def init_roadmap():
    """Initialisiert die Roadmap mit Standardwerten"""
    with app.app_context():
        # Prüfen, ob bereits Roadmap-Einträge vorhanden sind
        existing_items = RoadmapItem.query.count()
        if existing_items > 0:
            print(f"Es sind bereits {existing_items} Roadmap-Einträge vorhanden. Möchten Sie diese überschreiben? (j/n)")
            choice = input().lower().strip()
            if choice not in ['j', 'ja', 'y', 'yes']:
                print("Abbruch: Bestehende Einträge werden beibehalten.")
                return
            
            # Bestehende Einträge löschen
            RoadmapItem.query.delete()
            print("Bestehende Einträge wurden gelöscht.")
        
        # Kurzfristige Ziele
        short_term_items = [
            {
                "title": "E-Mail-Verifizierung verbessern",
                "description": "Automatischen E-Mail-Versand und Verifizierung optimieren",
                "status": "in_progress",
                "position": 0
            },
            {
                "title": "Mobile Ansicht optimieren",
                "description": "Responsive Design für alle Hauptfunktionen verbessern",
                "status": "planned",
                "position": 1
            },
            {
                "title": "Vergleich: Wirtschaftsplan vs. Ist-Kosten",
                "description": "Bessere visuelle Darstellung der Abweichungen",
                "status": "completed",
                "position": 2
            }
        ]
        
        # Mittelfristige Ziele
        medium_term_items = [
            {
                "title": "PWA-Funktionalität",
                "description": "Progressive Web App-Features implementieren für Offline-Nutzung",
                "status": "planned",
                "position": 0
            },
            {
                "title": "Dokumenten-Upload für Transaktionen",
                "description": "Rechnungen und Belege direkt an Transaktionen anhängen",
                "status": "in_progress",
                "position": 1
            },
            {
                "title": "Mehrere Abrechnungszeiträume verwalten",
                "description": "Parallele Verwaltung mehrerer Jahre mit Vergleichsfunktionen",
                "status": "planned",
                "position": 2
            }
        ]
        
        # Langfristige Ziele
        long_term_items = [
            {
                "title": "PostgreSQL-Integration",
                "description": "Umstellung auf PostgreSQL für bessere Performance",
                "status": "planned",
                "position": 0
            },
            {
                "title": "API-Schnittstelle",
                "description": "REST-API für Anbindung externer Dienste",
                "status": "planned",
                "position": 1
            },
            {
                "title": "Automatische Bankanbindung",
                "description": "Direkte Schnittstelle zu Online-Banking-APIs",
                "status": "planned",
                "position": 2
            }
        ]
        
        # Einträge zur Datenbank hinzufügen
        for item in short_term_items:
            db.session.add(RoadmapItem(
                title=item["title"],
                description=item["description"],
                status=item["status"],
                timeframe="short_term",
                position=item["position"]
            ))
        
        for item in medium_term_items:
            db.session.add(RoadmapItem(
                title=item["title"],
                description=item["description"],
                status=item["status"],
                timeframe="medium_term",
                position=item["position"]
            ))
        
        for item in long_term_items:
            db.session.add(RoadmapItem(
                title=item["title"],
                description=item["description"],
                status=item["status"],
                timeframe="long_term",
                position=item["position"]
            ))
        
        # Änderungen speichern
        db.session.commit()
        print(f"Roadmap wurde mit {len(short_term_items) + len(medium_term_items) + len(long_term_items)} Standardeinträgen initialisiert.")

if __name__ == "__main__":
    init_roadmap()
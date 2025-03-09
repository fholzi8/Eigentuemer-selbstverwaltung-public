"""
Skript zum Initialisieren des ersten Kontostands
"""

import os
import sys
import datetime
from decimal import Decimal
from flask import Flask

def init_kontostand(app):
    with app.app_context():
        from models import db, Kontostand
        from services.kontostand_service import get_current_kontostand
        
        # Prüfen, ob bereits ein Kontostand existiert
        current = get_current_kontostand()
        if current > 0:
            print(f"Es existiert bereits ein Kontostand: {current} €")
            return
        
        # Initialen Kontostand erstellen
        try:
            init_betrag = Decimal('2877.99')
            kontostand = Kontostand(
                datum=datetime.date.today(),
                betrag=init_betrag,
                kommentar="Initialer Kontostand",
                user_id=None  # Kein Benutzer (System)
            )
            
            db.session.add(kontostand)
            db.session.commit()
            
            print(f"Initialer Kontostand von {init_betrag} € erfolgreich erstellt.")
        except Exception as e:
            db.session.rollback()
            print(f"Fehler beim Erstellen des initialen Kontostands: {e}")

if __name__ == "__main__":
    # Flask-App erstellen
    from app import app
    init_kontostand(app)
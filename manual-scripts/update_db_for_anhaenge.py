# Datei: update_db_for_anhaenge.py

from app import app
from models import db, TransaktionAnhang
import os

def update_database():
    """
    Aktualisiert die Datenbank, um die TransaktionAnhang-Tabelle zu erstellen
    """
    with app.app_context():
        # Verzeichnis für Rechnungen erstellen
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'rechnungen')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Neue Tabelle erstellen
        db.create_all()
        
        print("Datenbank erfolgreich aktualisiert und Verzeichnis für Rechnungen erstellt.")

if __name__ == "__main__":
    update_database()
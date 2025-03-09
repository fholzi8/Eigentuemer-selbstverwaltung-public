# manual-scripts/migrate_to_postgres.py
import sys
import os
from pathlib import Path

# Pfad zum Projektverzeichnis hinzufügen
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app import app, db
from models import User, Miteigentuemer, Transaktion, Wirtschaftsplan, WirtschaftsplanMetadata, Kontostand

def migrate_data():
    """Migriert Daten von SQLite zu PostgreSQL"""
    # Ändere die Umgebungsvariable temporär
    os.environ['DATABASE_URL'] = 'sqlite:///weg_abrechnung.db'
    
    # Importiere die alte DB
    from flask_sqlalchemy import SQLAlchemy
    old_db = SQLAlchemy()
    
    class OldApp:
        config = {'SQLALCHEMY_DATABASE_URI': 'sqlite:///weg_abrechnung.db', 'SQLALCHEMY_TRACK_MODIFICATIONS': False}
        
    old_app = OldApp()
    old_db.init_app(old_app)
    
    # Hole Daten aus der alten DB
    # Implementiere hier die Datenextraktion...
    
    # Setze die Umgebungsvariable auf PostgreSQL
    os.environ['DATABASE_URL'] = 'postgresql://username:password@localhost:5432/wegapp'
    
    # Verwende die neue DB (aus app importiert)
    with app.app_context():
        # Füge Daten in die neue DB ein
        # Implementiere hier das Einfügen...
        
        db.session.commit()

if __name__ == "__main__":
    migrate_data()
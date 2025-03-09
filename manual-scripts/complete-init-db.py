# manual-scripts/complete_init_db.py
# Dieses Skript generiert ein vollständiges init_db.py Skript basierend auf der aktuellen Datenbankstruktur

import sys
import os
import inspect
from datetime import datetime

# Projektverzeichnis zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importiere die Anwendung und Modelle
from app import create_app
from models import db  # Stelle sicher, dass alle Modelle in models.py importiert werden

app = create_app()  # App erstellen

def generate_init_db_script():
    """
    Generiert ein vollständiges init_db.py Skript basierend auf den vorhandenen Modellen
    """
    # Sammle alle Modellklassen aus models.py
    from models import User  # Beispiel - importiere ein bekanntes Modell
    all_models = []
    
    # Finde alle Modellklassen im models-Modul
    module_name = User.__module__
    module = sys.modules[module_name]
    
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and hasattr(obj, '__tablename__'):
            all_models.append(obj)
    
    print(f"Gefundene Modelle: {[model.__name__ for model in all_models]}")
    
    # Erstelle das Skript
    script = f"""#!/usr/bin/env python
# init_db.py - Generiert am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Dieses Skript initialisiert die Datenbank für die WEG-Abrechnungsanwendung

import os
import sys
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from models import db
"""
    
    # Importiere alle Modelle
    script += "\n# Importiere alle Modelle\n"
    for model in all_models:
        script += f"from models import {model.__name__}\n"
    
    # Hauptfunktion
    script += """
def init_db():
    """Initialisiert die Datenbank mit Basisdaten"""
    app = create_app()
    
    with app.app_context():
        print("Lösche bestehende Tabellen...")
        db.drop_all()
        
        print("Erstelle Tabellen neu...")
        db.create_all()
        
        print("Füge Basisdaten ein...")
"""
    
    # Füge Code zum Erstellen von Standarddaten hinzu
    script += """        
        # Admin-Benutzer erstellen
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            password_hash=generate_password_hash('sichere5_Passwort!'),  # Ändere dies in ein sicheres Passwort!
            email='admin@example.com',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        
        # Beispiel-Miteigentümer erstellen (falls Miteigentuemer-Modell existiert)
        try:
            miteigentuemer1 = Miteigentuemer(
                name='Mustermann',
                vorname='Max',
                mea=100,  # Anpassen an deine Werte
                vf_einheiten=1,
                tg_einheiten=1
            )
            db.session.add(miteigentuemer1)
        except Exception as e:
            print(f"Fehler beim Erstellen von Beispiel-Miteigentümern: {e}")
        
        # Speichere die Änderungen
        db.session.commit()
        print("Datenbank wurde erfolgreich initialisiert!")

if __name__ == "__main__":
    init_db()
"""
    
    # Speichere das Skript in die Datei init_db.py
    with open('init_db.py', 'w') as f:
        f.write(script)
    
    print(f"Das Skript init_db.py wurde erstellt!")
    print("Hinweis: Passe das Skript an deine spezifischen Anforderungen an.")

if __name__ == "__main__":
    with app.app_context():
        generate_init_db_script()

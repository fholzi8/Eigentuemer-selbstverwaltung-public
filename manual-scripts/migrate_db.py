# migrate_db.py
import sqlite3
import os
from app import app

# Pfad zur Datenbankdatei
db_path = os.path.join(app.config['BASE_DIR'], 'weg_abrechnung.db')

def migrate_user_table():
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfen, ob die email-Spalte bereits existiert
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Wenn keine Migration notwendig ist
    if 'email' in columns:
        print("Tabelle bereits aktualisiert")
        conn.close()
        return
    
    print("Starte Migration der User-Tabelle...")
    
    # Transaktion starten
    conn.execute("BEGIN TRANSACTION")
    
    try:
        # Temporäre Tabelle mit neuem Schema erstellen
        cursor.execute('''
        CREATE TABLE user_new (
            id INTEGER PRIMARY KEY,
            username VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(150) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            email VARCHAR(150) UNIQUE,
            email_verified BOOLEAN DEFAULT FALSE,
            notify_transaction_changes BOOLEAN DEFAULT TRUE,
            notify_wirtschaftsplan_changes BOOLEAN DEFAULT TRUE,
            notify_user_changes BOOLEAN DEFAULT TRUE
        )
        ''')
        
        # Daten kopieren (nur die Spalten, die in beiden Tabellen existieren)
        cursor.execute('''
        INSERT INTO user_new (id, username, password_hash, is_admin)
        SELECT id, username, password_hash, is_admin FROM user
        ''')
        
        # Alte Tabelle löschen und neue umbenennen
        cursor.execute("DROP TABLE user")
        cursor.execute("ALTER TABLE user_new RENAME TO user")
        
        # Transaktion bestätigen
        conn.execute("COMMIT")
        print("Migration erfolgreich abgeschlossen")
    
    except Exception as e:
        # Bei Fehler: Transaktion zurückrollen
        conn.execute("ROLLBACK")
        print(f"Fehler bei der Migration: {e}")
    
    conn.close()

if __name__ == "__main__":
    migrate_user_table()
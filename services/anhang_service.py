"""
Service-Funktionen für Transaktionsanhänge
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

from models import db, TransaktionAnhang, Transaktion

def allowed_anhang_file(filename):
    """
    Prüft, ob die Dateiendung erlaubt ist
    
    Args:
        filename (str): Name der Datei
        
    Returns:
        bool: True, wenn die Dateiendung erlaubt ist
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_ANHANG_EXTENSIONS']

def save_anhang(file, transaktion_id):
    """
    Speichert einen Anhang für eine Transaktion
    
    Args:
        file: Das Datei-Objekt
        transaktion_id (int): ID der Transaktion
        
    Returns:
        tuple: (success, message, anhang_id)
    """
    try:
        # Prüfen, ob die Datei erlaubt ist
        if not file or not allowed_anhang_file(file.filename):
            return False, "Nicht unterstütztes Dateiformat. Erlaubt sind: PDF, JPG, JPEG, PNG.", None
        
        # Prüfen, ob die Transaktion existiert
        transaktion = Transaktion.query.get(transaktion_id)
        if not transaktion:
            return False, "Transaktion nicht gefunden.", None
        
        # Prüfen, ob bereits ein Anhang existiert
        existing_anhang = TransaktionAnhang.query.filter_by(transaktion_id=transaktion_id).first()
        if existing_anhang:
            # Alten Anhang löschen
            try:
                os.remove(existing_anhang.get_file_path())
            except Exception as e:
                # Fehler beim Löschen der alten Datei ignorieren
                pass
                
            db.session.delete(existing_anhang)
            db.session.commit()
        
        # Dateiendung extrahieren
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # Neuen Dateinamen generieren
        new_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Verzeichnis erstellen, falls es nicht existiert
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'rechnungen')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Datei speichern
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        # Anhang in der Datenbank speichern
        anhang = TransaktionAnhang(
            transaktion_id=transaktion_id,
            dateiname=new_filename,
            original_dateiname=original_filename,
            dateityp=file_extension
        )
        
        db.session.add(anhang)
        db.session.commit()
        
        return True, "Rechnung erfolgreich hochgeladen.", anhang.id
    except Exception as e:
        db.session.rollback()
        return False, f"Fehler beim Hochladen der Rechnung: {str(e)}", None

def delete_anhang(anhang_id):
    """
    Löscht einen Anhang
    
    Args:
        anhang_id (int): ID des Anhangs
        
    Returns:
        tuple: (success, message)
    """
    try:
        anhang = TransaktionAnhang.query.get(anhang_id)
        
        if not anhang:
            return False, "Anhang nicht gefunden."
        
        # Datei löschen
        try:
            os.remove(anhang.get_file_path())
        except Exception as e:
            # Fehler beim Löschen der Datei ignorieren
            pass
        
        # Anhang aus der Datenbank löschen
        db.session.delete(anhang)
        db.session.commit()
        
        return True, "Rechnung erfolgreich gelöscht."
    except Exception as e:
        db.session.rollback()
        return False, f"Fehler beim Löschen der Rechnung: {str(e)}"
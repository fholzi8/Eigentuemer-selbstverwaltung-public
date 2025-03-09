"""
Skript zum Erstellen eines Admin-Benutzers für die Ersteinrichtung
"""

import os
import sys
import getpass
from flask import Flask
from models import db, User

def create_admin_user(app):
    with app.app_context():
        # Prüfen, ob bereits ein Admin-Benutzer existiert
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            print(f"Es existiert bereits ein Admin-Benutzer: {existing_admin.username}")
            return
        
        # Admin-Benutzer erstellen
        print("Admin-Benutzer erstellen")
        username = input("Benutzername: ")
        
        # Prüfen, ob Benutzer bereits existiert
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Ein Benutzer mit dem Namen '{username}' existiert bereits.")
            return
        
        # Sicheres Passwort eingeben (wird nicht angezeigt)
        password = getpass.getpass("Passwort: ")
        password_confirm = getpass.getpass("Passwort bestätigen: ")
        
        if password != password_confirm:
            print("Die Passwörter stimmen nicht überein.")
            return
        
        if len(password) < 8:
            print("Das Passwort sollte mindestens 8 Zeichen lang sein.")
            confirm = input("Trotzdem fortfahren? (j/n): ")
            if confirm.lower() != 'j':
                return
        
        # Neuen Admin-Benutzer erstellen
        admin = User(username=username, is_admin=True)
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"Admin-Benutzer '{username}' erfolgreich erstellt.")
        except Exception as e:
            db.session.rollback()
            print(f"Fehler beim Erstellen des Admin-Benutzers: {str(e)}")

if __name__ == "__main__":
    # Flask-App erstellen
    from app import app
    create_admin_user(app)
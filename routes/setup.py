"""
Setup-Blueprint für die Ersteinrichtung der Anwendung
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import os
import secrets
import re
from pathlib import Path

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

@setup_bp.route('/', methods=['GET', 'POST'])
def index():
    """Setup-Routine für die erste Konfiguration"""
    # Prüfen, ob SECRET_KEY bereits gesetzt ist
    secret_key = current_app.config.get('SECRET_KEY')
    if secret_key is not None and secret_key not in ['development', 'default_key', '', None]:
        # Falls SECRET_KEY bereits gesetzt ist, Weiterleitung zur Startseite
        flash('Die Anwendung ist bereits eingerichtet.', 'info')
        return redirect(url_for('dashboard.root'))
    
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        generate_new = 'generate' in request.form
        
        if generate_new:
            # Generiere einen zufälligen SECRET_KEY
            secret_key = secrets.token_hex(32)
        
        if secret_key:
            # Speichere SECRET_KEY in .env-Datei
            try:
                # Pfad zur .env-Datei
                env_path = Path('.env')
                
                # Inhalt der Datei lesen, falls sie existiert
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        content = f.read()
                else:
                    content = ''
                
                # Prüfen, ob SECRET_KEY bereits in der Datei vorhanden ist
                if 'SECRET_KEY' in content:
                    # SECRET_KEY aktualisieren
                    new_content = re.sub(r'SECRET_KEY=[^\n]*', f'SECRET_KEY="{secret_key}"', content)
                else:
                    # SECRET_KEY hinzufügen
                    new_content = content
                    if new_content and not new_content.endswith('\n'):
                        new_content += '\n'
                    new_content += f'SECRET_KEY="{secret_key}"\n'
                
                # Datei schreiben
                with open(env_path, 'w') as f:
                    f.write(new_content)
                
                # Erfolg melden
                flash('SECRET_KEY wurde erfolgreich gespeichert. Die Anwendung muss neu gestartet werden.', 'success')
                
                # Neustart der Anwendung in Produktionsumgebungen könnte hier automatisch erfolgen
                # Dies ist jedoch umgebungsabhängig und oft nicht möglich
                
                return render_template('setup/restart.html', secret_key=secret_key)
            except Exception as e:
                flash(f'Fehler beim Speichern des SECRET_KEY: {str(e)}', 'danger')
    
    return render_template('setup/index.html')
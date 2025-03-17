"""
Vorlagen-Blueprint zur Verwaltung von Brief-Vorlagen, Tagesordnungspunkten und wichtigen Dokumenten
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import datetime
from sqlalchemy import desc

from models import db, BriefVorlage, TagesordnungspunktVorlage, WichtigesDokument, Miteigentuemer, User
from services.vorlagen_service import get_brief_vorlagen, get_tops, get_wichtige_dokumente
from services.anhang_service import save_anhang, delete_anhang

vorlagen_bp = Blueprint('vorlagen', __name__, url_prefix='/vorlagen')

# Routen für Brief-Vorlagen
@vorlagen_bp.route('/briefe', methods=['GET'])
@login_required
def briefe_liste():
    """Liste aller Brief-Vorlagen"""
    vorlagen = BriefVorlage.query.order_by(BriefVorlage.titel).all()
    return render_template('vorlagen/briefe/liste.html', vorlagen=vorlagen)

@vorlagen_bp.route('/briefe/neu', methods=['GET', 'POST'])
@login_required
def brief_neu():
    """Neue Brief-Vorlage erstellen"""
    miteigentuemer = Miteigentuemer.query.all()
    
    if request.method == 'POST':
        titel = request.form.get('titel')
        typ = request.form.get('typ')
        inhalt = request.form.get('inhalt')
        
        vorlage = BriefVorlage(
            titel=titel,
            typ=typ,
            inhalt=inhalt,
            erstellt_von=current_user.id,
            erstellt_am=datetime.datetime.now()
        )
        
        try:
            db.session.add(vorlage)
            db.session.commit()
            flash('Brief-Vorlage erfolgreich erstellt', 'success')
            return redirect(url_for('vorlagen.briefe_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen der Vorlage: {str(e)}', 'danger')
    
    return render_template('vorlagen/briefe/neu.html', miteigentuemer=miteigentuemer)

@vorlagen_bp.route('/briefe/<int:vorlage_id>', methods=['GET', 'POST'])
@login_required
def brief_bearbeiten(vorlage_id):
    """Brief-Vorlage bearbeiten"""
    vorlage = BriefVorlage.query.get_or_404(vorlage_id)
    miteigentuemer = Miteigentuemer.query.all()
    
    if request.method == 'POST':
        vorlage.titel = request.form.get('titel')
        vorlage.typ = request.form.get('typ')
        vorlage.inhalt = request.form.get('inhalt')
        vorlage.aktualisiert_am = datetime.datetime.now()
        
        try:
            db.session.commit()
            flash('Brief-Vorlage erfolgreich aktualisiert', 'success')
            return redirect(url_for('vorlagen.briefe_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren der Vorlage: {str(e)}', 'danger')
    
    return render_template('vorlagen/briefe/bearbeiten.html', vorlage=vorlage, miteigentuemer=miteigentuemer)

@vorlagen_bp.route('/briefe/<int:vorlage_id>/vorschau', methods=['GET'])
@login_required
def brief_vorschau(vorlage_id):
    """Brief-Vorlage anzeigen mit Platzhaltern ersetzt durch echte Daten"""
    vorlage = BriefVorlage.query.get_or_404(vorlage_id)
    miteigentuemer = Miteigentuemer.query.all()
    
    # Hier Platzhalter durch echte Daten ersetzen
    vorschau_inhalt = vorlage.inhalt
    # z.B. {{datum}} durch aktuelles Datum ersetzen
    vorschau_inhalt = vorschau_inhalt.replace('{{datum}}', datetime.datetime.now().strftime('%d.%m.%Y'))
    
    return render_template('vorlagen/briefe/vorschau.html', vorlage=vorlage, inhalt=vorschau_inhalt)

@vorlagen_bp.route('/briefe/<int:vorlage_id>/delete', methods=['POST'])
@login_required
def brief_loeschen(vorlage_id):
    """Brief-Vorlage löschen"""
    vorlage = BriefVorlage.query.get_or_404(vorlage_id)
    
    try:
        db.session.delete(vorlage)
        db.session.commit()
        flash('Brief-Vorlage erfolgreich gelöscht', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen der Vorlage: {str(e)}', 'danger')
    
    return redirect(url_for('vorlagen.briefe_liste'))

# Routen für Tagesordnungspunkte
@vorlagen_bp.route('/tops', methods=['GET'])
@login_required
def tops_liste():
    """Liste aller Tagesordnungspunkt-Vorlagen"""
    # Filter für Status
    filter_status = request.args.get('status', 'aktiv')
    
    if filter_status == 'alle':
        tops = TagesordnungspunktVorlage.query.order_by(TagesordnungspunktVorlage.position).all()
    else:
        tops = TagesordnungspunktVorlage.query.filter_by(status=filter_status).order_by(TagesordnungspunktVorlage.position).all()
    
    return render_template('vorlagen/tops/liste.html', tops=tops, filter_status=filter_status)

@vorlagen_bp.route('/tops/neu', methods=['GET', 'POST'])
@login_required
def top_neu():
    """Neuen Tagesordnungspunkt erstellen"""
    if request.method == 'POST':
        titel = request.form.get('titel')
        beschreibung = request.form.get('beschreibung')
        position = request.form.get('position', 0, type=int)
        status = request.form.get('status', 'aktiv')
        
        top = TagesordnungspunktVorlage(
            titel=titel,
            beschreibung=beschreibung,
            position=position,
            status=status,
            erstellt_von=current_user.id,
            erstellt_am=datetime.datetime.now()
        )
        
        try:
            db.session.add(top)
            db.session.commit()
            flash('Tagesordnungspunkt erfolgreich erstellt', 'success')
            return redirect(url_for('vorlagen.tops_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen des Tagesordnungspunkts: {str(e)}', 'danger')
    
    return render_template('vorlagen/tops/neu.html')

@vorlagen_bp.route('/tops/<int:top_id>', methods=['GET', 'POST'])
@login_required
def top_bearbeiten(top_id):
    """Tagesordnungspunkt bearbeiten"""
    top = TagesordnungspunktVorlage.query.get_or_404(top_id)
    
    if request.method == 'POST':
        top.titel = request.form.get('titel')
        top.beschreibung = request.form.get('beschreibung')
        top.position = request.form.get('position', 0, type=int)
        top.status = request.form.get('status', 'aktiv')
        top.aktualisiert_am = datetime.datetime.now()
        
        try:
            db.session.commit()
            flash('Tagesordnungspunkt erfolgreich aktualisiert', 'success')
            return redirect(url_for('vorlagen.tops_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren des Tagesordnungspunkts: {str(e)}', 'danger')
    
    return render_template('vorlagen/tops/bearbeiten.html', top=top)

@vorlagen_bp.route('/tops/<int:top_id>/delete', methods=['POST'])
@login_required
def top_loeschen(top_id):
    """Tagesordnungspunkt löschen"""
    top = TagesordnungspunktVorlage.query.get_or_404(top_id)
    
    try:
        db.session.delete(top)
        db.session.commit()
        flash('Tagesordnungspunkt erfolgreich gelöscht', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen des Tagesordnungspunkts: {str(e)}', 'danger')
    
    return redirect(url_for('vorlagen.tops_liste'))

# Routen für Wichtige Dokumente
@vorlagen_bp.route('/dokumente', methods=['GET'])
@login_required
def dokumente_liste():
    """Liste aller wichtigen Dokumente"""
    # Filter für Kategorie
    filter_kategorie = request.args.get('kategorie', '')
    
    if filter_kategorie:
        dokumente = WichtigesDokument.query.filter_by(kategorie=filter_kategorie).order_by(WichtigesDokument.titel).all()
    else:
        dokumente = WichtigesDokument.query.order_by(WichtigesDokument.kategorie, WichtigesDokument.titel).all()
    
    # Alle verfügbaren Kategorien für Filter
    kategorien = db.session.query(WichtigesDokument.kategorie).distinct().all()
    kategorien = [k[0] for k in kategorien if k[0] is not None]
    
    return render_template('vorlagen/dokumente/liste.html', dokumente=dokumente, 
                          kategorien=kategorien, filter_kategorie=filter_kategorie)

@vorlagen_bp.route('/dokumente/neu', methods=['GET', 'POST'])
@login_required
def dokument_neu():
    """Neues wichtiges Dokument hochladen"""
    if request.method == 'POST':
        titel = request.form.get('titel')
        beschreibung = request.form.get('beschreibung')
        kategorie = request.form.get('kategorie')
        
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Keine Datei ausgewählt', 'danger')
            return redirect(request.url)
        
        # Datei speichern und Dokument erstellen
        try:
            # Datei speichern
            filename = secure_filename(file.filename)
            datei_pfad = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dokumente', filename)
            os.makedirs(os.path.dirname(datei_pfad), exist_ok=True)
            file.save(datei_pfad)
            
            # Dateityp ermitteln
            dateityp = os.path.splitext(filename)[1][1:].lower()
            
            # Dokument erstellen
            dokument = WichtigesDokument(
                titel=titel,
                beschreibung=beschreibung,
                kategorie=kategorie,
                dateiname=filename,
                original_dateiname=file.filename,
                dateityp=dateityp,
                hochgeladen_von=current_user.id,
                hochgeladen_am=datetime.datetime.now()
            )
            
            db.session.add(dokument)
            db.session.commit()
            
            flash('Dokument erfolgreich hochgeladen', 'success')
            return redirect(url_for('vorlagen.dokumente_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Hochladen des Dokuments: {str(e)}', 'danger')
    
    return render_template('vorlagen/dokumente/neu.html')

@vorlagen_bp.route('/dokumente/<int:dokument_id>', methods=['GET', 'POST'])
@login_required
def dokument_bearbeiten(dokument_id):
    """Wichtiges Dokument bearbeiten (nur Metadaten)"""
    dokument = WichtigesDokument.query.get_or_404(dokument_id)
    
    if request.method == 'POST':
        dokument.titel = request.form.get('titel')
        dokument.beschreibung = request.form.get('beschreibung')
        dokument.kategorie = request.form.get('kategorie')
        
        try:
            db.session.commit()
            flash('Dokument erfolgreich aktualisiert', 'success')
            return redirect(url_for('vorlagen.dokumente_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren des Dokuments: {str(e)}', 'danger')
    
    return render_template('vorlagen/dokumente/bearbeiten.html', dokument=dokument)

@vorlagen_bp.route('/dokumente/<int:dokument_id>/view')
@login_required
def dokument_anzeigen(dokument_id):
    """Dokument im Browser anzeigen"""
    dokument = WichtigesDokument.query.get_or_404(dokument_id)
    
    from flask import send_file
    return send_file(
        dokument.get_file_path(),
        download_name=dokument.original_dateiname,
        as_attachment=False
    )

@vorlagen_bp.route('/dokumente/<int:dokument_id>/download')
@login_required
def dokument_download(dokument_id):
    """Dokument herunterladen"""
    dokument = WichtigesDokument.query.get_or_404(dokument_id)
    
    from flask import send_file
    return send_file(
        dokument.get_file_path(),
        download_name=dokument.original_dateiname,
        as_attachment=True
    )

@vorlagen_bp.route('/dokumente/<int:dokument_id>/delete', methods=['POST'])
@login_required
def dokument_loeschen(dokument_id):
    """Wichtiges Dokument löschen"""
    dokument = WichtigesDokument.query.get_or_404(dokument_id)
    
    try:
        # Datei löschen
        os.remove(dokument.get_file_path())
        
        # Datensatz löschen
        db.session.delete(dokument)
        db.session.commit()
        
        flash('Dokument erfolgreich gelöscht', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen des Dokuments: {str(e)}', 'danger')
    
    return redirect(url_for('vorlagen.dokumente_liste'))
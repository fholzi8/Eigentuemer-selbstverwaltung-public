"""
Wirtschaftsplan-Blueprint zur Verwaltung von Wirtschaftsplänen
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
import datetime
from decimal import Decimal
import os
from werkzeug.utils import secure_filename

from models import db, Wirtschaftsplan, Miteigentuemer, WirtschaftsplanMetadata, Transaktion, User 
from services.wirtschaftsplan_service import get_wirtschaftsplan_data, import_wirtschaftsplan, get_actual_costs
from utils import allowed_file, parse_german_date  # direkt aus utils importieren

wirtschaftsplan_bp = Blueprint('wirtschaftsplan', __name__, url_prefix='/wirtschaftsplan')

@wirtschaftsplan_bp.route('/', methods=['GET'])
@login_required
def uebersicht():
    # Verfügbare Jahre für Wirtschaftspläne
    wp_jahre = db.session.query(Wirtschaftsplan.jahr).distinct().order_by(Wirtschaftsplan.jahr.desc()).all()
    wp_jahre = [j[0] for j in wp_jahre]
    
    # Verfügbare Jahre für Transaktionen (um tatsächliche Kosten zu berücksichtigen)
    tx_jahre = db.session.query(Transaktion.jahr).distinct().order_by(Transaktion.jahr.desc()).all()
    tx_jahre = [j[0] for j in tx_jahre]
    
    # Kombiniere alle verfügbaren Jahre
    alle_jahre = list(set(wp_jahre + tx_jahre))
    alle_jahre.sort(reverse=True)
    
    # Ergänze mit aktuellen und vergangenen Jahren, falls nicht in der Liste
    current_year = datetime.date.today().year
    for year in range(current_year - 1, current_year + 2):
        if year not in alle_jahre:
            alle_jahre.append(year)
    alle_jahre.sort(reverse=True)
    
    # Jahr aus Session oder Request-Args
    if 'reset_filters' in request.args:
        session.pop('wirtschaftsplan_jahr', None)
    
    # Filter aus Request oder Session laden
    jahr = request.args.get('jahr', session.get('wirtschaftsplan_jahr', datetime.date.today().year), type=int)
    
    # Aktuelles Jahr in der Session speichern
    session['wirtschaftsplan_jahr'] = jahr
    
    # Wirtschaftsplandaten abrufen
    wirtschaftsplan_data = get_wirtschaftsplan_data(jahr)
    
    # Tatsächliche Kosten für den Vergleich abrufen (aus der Transaktion-Tabelle)
    tatsaechliche_kosten = get_actual_costs(jahr)
    
    return render_template(
        'wirtschaftsplan/uebersicht.html',
        jahre=alle_jahre,
        jahr=jahr,
        eintraege=wirtschaftsplan_data['eintraege'],
        kategorien=wirtschaftsplan_data['kategorien'],
        metadata=wirtschaftsplan_data['metadata'],
        summen=wirtschaftsplan_data['summen'],
        miteigentuemer_anteile=wirtschaftsplan_data['miteigentuemer_anteile'],
        tatsaechliche_kosten=tatsaechliche_kosten
    )

@wirtschaftsplan_bp.route('/neu', methods=['GET', 'POST'])
@login_required
def neu():
    if request.method == 'POST':
        try:
            jahr = request.form.get('jahr', type=int)
            bezeichnung = request.form.get('bezeichnung')
            kategorie = request.form.get('kategorie')
            betrag_str = request.form.get('betrag').replace(',', '.')
            betrag = Decimal(betrag_str)
            verteilungsschluessel = request.form.get('verteilungsschluessel')
            umlagefaehig = 'umlagefaehig' in request.form
            notiz = request.form.get('notiz', '')
            
            # Prüfen, ob bereits ein Wirtschaftsplan für dieses Jahr existiert
            metadata = WirtschaftsplanMetadata.query.filter_by(jahr=jahr).first()
            if not metadata:
                metadata = WirtschaftsplanMetadata(
                    jahr=jahr,
                    importiert_am=datetime.datetime.now(),
                    importiert_von=current_user.id if current_user.is_authenticated else None,
                    dateiname="Manuell erstellt",
                    status="aktiv"
                )
                db.session.add(metadata)
            
            eintrag = Wirtschaftsplan(
                jahr=jahr,
                bezeichnung=bezeichnung,
                kategorie=kategorie,
                betrag=betrag,
                verteilungsschluessel=verteilungsschluessel,
                umlagefaehig=umlagefaehig,
                notiz=notiz
            )
            
            db.session.add(eintrag)
            db.session.commit()
            
            flash('Wirtschaftsplan-Eintrag erfolgreich hinzugefügt')
            return redirect(url_for('wirtschaftsplan.uebersicht', jahr=jahr))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen des Wirtschaftsplan-Eintrags: {str(e)}')
    
    # Verfügbare Jahre dynamisch ermitteln (aktuelles Jahr + 2 Jahre in die Vergangenheit + 1 Jahr in die Zukunft)
    current_year = datetime.date.today().year
    jahre = list(range(current_year - 2, current_year + 2))
    
    # Zusätzlich alle Jahre abfragen, für die bereits Transaktionen existieren
    tx_jahre = db.session.query(Transaktion.jahr).distinct().all()
    tx_jahre = [j[0] for j in tx_jahre]
    
    # Jahre kombinieren und doppelte entfernen
    alle_jahre = sorted(set(jahre + tx_jahre), reverse=True)
    
    return render_template('wirtschaftsplan/neu.html', jahre=alle_jahre)

@wirtschaftsplan_bp.route('/<int:eintrag_id>', methods=['GET', 'POST'])
@login_required
def bearbeiten(eintrag_id):
    eintrag = Wirtschaftsplan.query.get_or_404(eintrag_id)
    
    if request.method == 'POST':
        try:
            eintrag.bezeichnung = request.form.get('bezeichnung')
            eintrag.kategorie = request.form.get('kategorie')
            betrag_str = request.form.get('betrag').replace(',', '.')
            eintrag.betrag = Decimal(betrag_str)
            eintrag.verteilungsschluessel = request.form.get('verteilungsschluessel')
            eintrag.umlagefaehig = 'umlagefaehig' in request.form
            eintrag.notiz = request.form.get('notiz', '')
            
            db.session.commit()
            
            flash('Wirtschaftsplan-Eintrag erfolgreich aktualisiert')
            return redirect(url_for('wirtschaftsplan.uebersicht', jahr=eintrag.jahr))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren des Wirtschaftsplan-Eintrags: {str(e)}')
    
    return render_template('wirtschaftsplan/bearbeiten.html', eintrag=eintrag)

@wirtschaftsplan_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        file = request.files['file']
        jahr = request.form.get('jahr', type=int)
        
        if file.filename == '':
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        if not jahr:
            flash('Bitte ein Jahr angeben')
            return redirect(request.url)
        
        if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Importieren
            success, message, count = import_wirtschaftsplan(file_path, jahr, current_user.id)
            
            if success:
                flash(f'{count} Wirtschaftsplan-Einträge erfolgreich importiert')
                return redirect(url_for('wirtschaftsplan.uebersicht', jahr=jahr))
            else:
                flash(f'Fehler beim Import: {message}')
                return redirect(request.url)
        else:
            flash('Nicht unterstütztes Dateiformat')
    
    # Verfügbare Jahre dynamisch ermitteln (aktuelles Jahr + 2 Jahre in die Vergangenheit + 1 Jahr in die Zukunft)
    current_year = datetime.date.today().year
    jahre = list(range(current_year - 2, current_year + 2))
    
    # Zusätzlich alle Jahre abfragen, für die bereits Transaktionen existieren
    tx_jahre = db.session.query(Transaktion.jahr).distinct().all()
    tx_jahre = [j[0] for j in tx_jahre]
    
    # Jahre kombinieren und doppelte entfernen
    alle_jahre = sorted(set(jahre + tx_jahre), reverse=True)
    
    return render_template('wirtschaftsplan/import.html', jahre=alle_jahre)

@wirtschaftsplan_bp.route('/delete/<int:eintrag_id>', methods=['POST'])
@login_required
def delete(eintrag_id):
    eintrag = Wirtschaftsplan.query.get_or_404(eintrag_id)
    jahr = eintrag.jahr
    
    try:
        db.session.delete(eintrag)
        db.session.commit()
        flash('Wirtschaftsplan-Eintrag erfolgreich gelöscht')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen des Wirtschaftsplan-Eintrags: {str(e)}')
    
    return redirect(url_for('wirtschaftsplan.uebersicht', jahr=jahr))

@wirtschaftsplan_bp.route('/metadata/<int:jahr>', methods=['POST'])
@login_required
def update_metadata(jahr):
    metadata = WirtschaftsplanMetadata.query.filter_by(jahr=jahr).first()
    
    if not metadata:
        metadata = WirtschaftsplanMetadata(
            jahr=jahr,
            importiert_am=datetime.datetime.now(),
            importiert_von=current_user.id if current_user.is_authenticated else None,
            dateiname="Manuell erstellt",
            status="aktiv"
        )
        db.session.add(metadata)
    
    metadata.status = request.form.get('status', 'aktiv')
    
    try:
        db.session.commit()
        
        # E-Mail-Benachrichtigung senden
        from utils.email_utils import send_wirtschaftsplan_notification
        for user in User.query.filter_by(is_admin=True).all():
            send_wirtschaftsplan_notification(user, metadata, f"Status auf '{metadata.status}' geändert")
        
        flash('Status des Wirtschaftsplans aktualisiert')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Aktualisieren des Status: {str(e)}')
    
    return redirect(url_for('wirtschaftsplan.uebersicht', jahr=jahr))
    '''
    try:
        db.session.commit()
        flash('Status des Wirtschaftsplans aktualisiert')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Aktualisieren des Status: {str(e)}')
    
    return redirect(url_for('wirtschaftsplan.uebersicht', jahr=jahr))
    '''
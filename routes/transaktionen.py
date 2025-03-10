"""
Transaktionen-Blueprint zur Verwaltung von Banktransaktionen
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import datetime
from decimal import Decimal

from models import db, Transaktion, Miteigentuemer, User

from utils import allowed_file, kategorisiere_transaktion, parse_german_date, importiere_csv
from services.transaktion_service import get_filtered_transaktionen, get_transaction_statistics
from services.anhang_service import save_anhang, delete_anhang


transaktionen_bp = Blueprint('transaktionen', __name__, url_prefix='/transaktionen')

@transaktionen_bp.route('/', methods=['GET'])
@login_required
def liste():
    # Seitennummer und Anzahl pro Seite aus Request oder Session laden
    page = request.args.get('page', session.get('transaktionen_page', 1), type=int)
    per_page = request.args.get('per_page', session.get('transaktionen_per_page', 20), type=int)
    
    # Filter aus der Session laden oder aus den Request-Args
    if 'reset_filters' in request.args:
        # Wenn explizit ein Reset angefordert wird, Filter zurücksetzen
        session.pop('filter_kostenart', None)
        session.pop('filter_umlagefaehig', None)
        session.pop('filter_verteilungsschluessel', None)
        session.pop('filter_transaktionstyp', None)
        session.pop('filter_jahr', None)
        session.pop('transaktionen_page', None)
        session.pop('transaktionen_per_page', None)
        # Zurück zu Standardwerten
        page = 1
        per_page = 20
    
    # Filter aus Request oder Session laden
    filter_kostenart = request.args.get('kostenart', session.get('filter_kostenart', ''))
    filter_umlagefaehig = request.args.get('umlagefaehig', session.get('filter_umlagefaehig', ''))
    filter_verteilungsschluessel = request.args.get('verteilungsschluessel', session.get('filter_verteilungsschluessel', ''))
    filter_transaktionstyp = request.args.get('transaktionstyp', session.get('filter_transaktionstyp', ''))
    filter_jahr = request.args.get('jahr', session.get('filter_jahr', datetime.date.today().year), type=int)
    
    # Aktuelle Filter in der Session speichern
    session['filter_kostenart'] = filter_kostenart
    session['filter_umlagefaehig'] = filter_umlagefaehig
    session['filter_verteilungsschluessel'] = filter_verteilungsschluessel
    session['filter_transaktionstyp'] = filter_transaktionstyp
    session['filter_jahr'] = filter_jahr
    session['transaktionen_page'] = page
    session['transaktionen_per_page'] = per_page
    
    # Service-Funktionen aufrufen für gefilterte Transaktionen
    query = Transaktion.query.filter(Transaktion.jahr == filter_jahr)
    
    # Filter für Transaktionstyp (Einzahlungen/Ausgaben)
    if filter_transaktionstyp == 'einzahlungen':
        query = query.filter(Transaktion.betrag > 0)
    elif filter_transaktionstyp == 'ausgaben':
        query = query.filter(Transaktion.betrag < 0)
    
    if filter_kostenart:
        query = query.filter(Transaktion.kostenart == filter_kostenart)
    
    if filter_umlagefaehig:
        umlagefaehig_bool = (filter_umlagefaehig == 'ja')
        query = query.filter(Transaktion.umlagefaehig == umlagefaehig_bool)
    
    if filter_verteilungsschluessel:
        query = query.filter(Transaktion.verteilungsschluessel == filter_verteilungsschluessel)
    
    # Sortieren und paginieren
    # Spezialfall: per_page=0 bedeutet "alle anzeigen"
    if per_page > 0:
        transaktionen = query.order_by(Transaktion.datum.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        # Keine Paginierung, alle anzeigen
        # Hier müssen wir eine manuelle "Paginator-ähnliche" Struktur erstellen
        all_transactions = query.order_by(Transaktion.datum.desc()).all()
        
        # Erstellen eines Mock-Paginator-Objekts
        class MockPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = 1
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                return [1]
        
        transaktionen = MockPagination(all_transactions, 1, len(all_transactions), len(all_transactions))
    
    # Statistiken für das Jahr abrufen
    stats = get_transaction_statistics(filter_jahr)
    
    # Kostenarten für Filter
    kostenarten = db.session.query(Transaktion.kostenart).distinct().all()
    kostenarten = [k[0] for k in kostenarten if k[0] is not None]
    
    # Verteilungsschlüssel für Filter
    verteilungsschluessel = db.session.query(Transaktion.verteilungsschluessel).distinct().all()
    verteilungsschluessel = [v[0] for v in verteilungsschluessel if v[0] is not None]
    
    # Verfügbare Jahre
    jahre = db.session.query(Transaktion.jahr).distinct().order_by(Transaktion.jahr.desc()).all()
    jahre = [j[0] for j in jahre]
    
    return render_template(
        'transaktionen/liste.html', 
        transaktionen=transaktionen,
        kostenarten=kostenarten,
        verteilungsschluessel=verteilungsschluessel,
        jahre=jahre,
        filter_kostenart=filter_kostenart,
        filter_umlagefaehig=filter_umlagefaehig,
        filter_verteilungsschluessel=filter_verteilungsschluessel,
        filter_transaktionstyp=filter_transaktionstyp,
        filter_jahr=filter_jahr,
        per_page=per_page,
        summe_einnahmen=stats['summe_einnahmen'],
        summe_ausgaben=stats['summe_ausgaben']
    )

@transaktionen_bp.route('/<int:transaktion_id>/delete', methods=['POST'])
@login_required
def delete(transaktion_id):
    """
    Löscht eine Transaktion
    """
    transaktion = Transaktion.query.get_or_404(transaktion_id)
    
    try:
        # Speichern des Jahres für die Weiterleitung
        jahr = transaktion.jahr
        
        # Löschen der Transaktion
        db.session.delete(transaktion)
        db.session.commit()
        
        # E-Mail-Benachrichtigung senden
        try:
            from utils.email_utils import send_transaction_notification
            admin_users = User.query.filter_by(is_admin=True).all()
            print(f"Admin-Benutzer gefunden: {len(admin_users)}")
               
            for user in admin_users:
                print(f"Versuche E-Mail zu senden an: {user.username}, E-Mail: {getattr(user, 'email', 'Keine E-Mail')}")
                if hasattr(user, 'email') and user.email:
                    try:
                        send_transaction_notification(user, transaktion, "aktualisiert")
                        print(f"E-Mail an {user.email} gesendet")
                    except Exception as mail_error:
                        print(f"Fehler beim Senden der E-Mail an {user.email}: {str(mail_error)}")
                else:
                    print(f"Benutzer {user.username} hat keine E-Mail-Adresse")
        except Exception as e:
            print(f"Allgemeiner Fehler bei E-Mail-Benachrichtigung: {str(e)}")

        flash('Transaktion erfolgreich gelöscht', 'success')
        
        # Zurück zur Liste mit denselben Filtereinstellungen und Seite
        page = session.get('transaktionen_page', 1)
        per_page = session.get('transaktionen_per_page', 20)
        
        return redirect(url_for('transaktionen.liste', 
                               jahr=jahr, 
                               page=page,
                               per_page=per_page))
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen der Transaktion: {str(e)}', 'danger')
        return redirect(url_for('transaktionen.liste'))

@transaktionen_bp.route('/<int:transaktion_id>', methods=['GET', 'POST'])
@login_required
def bearbeiten(transaktion_id):
    """
    Bearbeitet eine Transaktion und kehrt zur vorherigen Seite zurück
    """
    transaktion = Transaktion.query.get_or_404(transaktion_id)
    miteigentuemer = Miteigentuemer.query.all()
    
    if request.method == 'POST':
        transaktion.beschreibung = request.form.get('beschreibung')
        transaktion.kategorie = request.form.get('kategorie')
        transaktion.kostenart = request.form.get('kostenart')
        transaktion.umlagefaehig = 'umlagefaehig' in request.form
        transaktion.verteilungsschluessel = request.form.get('verteilungsschluessel', 'Einheiten')
        
        # Miteigentümer nur für Einzahlungen setzen
        if transaktion.betrag > 0 and request.form.get('miteigentuemer'):
            transaktion.miteigentuemer_id = int(request.form.get('miteigentuemer'))
        else:
            transaktion.miteigentuemer_id = None
        
        try:
            db.session.commit()

            # E-Mail-Benachrichtigung senden
            try:
                from utils.email_utils import send_transaction_notification
                admin_users = User.query.filter_by(is_admin=True).all()
                print(f"Admin-Benutzer gefunden: {len(admin_users)}")
                
                for user in admin_users:
                    print(f"Versuche E-Mail zu senden an: {user.username}, E-Mail: {getattr(user, 'email', 'Keine E-Mail')}")
                    if hasattr(user, 'email') and user.email:
                        try:
                            send_transaction_notification(user, transaktion, "aktualisiert")
                            print(f"E-Mail an {user.email} gesendet")
                        except Exception as mail_error:
                            print(f"Fehler beim Senden der E-Mail an {user.email}: {str(mail_error)}")
                    else:
                        print(f"Benutzer {user.username} hat keine E-Mail-Adresse")
            except Exception as e:
                print(f"Allgemeiner Fehler bei E-Mail-Benachrichtigung: {str(e)}")

            flash('Transaktion aktualisiert', 'success')
            
            # Zurück zur Liste mit denselben Filtereinstellungen und Seite
            page = session.get('transaktionen_page', 1)
            per_page = session.get('transaktionen_per_page', 20)
            
            return redirect(url_for('transaktionen.liste', 
                                   page=page,
                                   per_page=per_page))
                                   
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'danger')
    
    return render_template(
        'transaktionen/bearbeiten.html', 
        transaktion=transaktion, 
        miteigentuemer=miteigentuemer
    )

@transaktionen_bp.route('/neu', methods=['GET', 'POST'])
@login_required
def neu():
    miteigentuemer = Miteigentuemer.query.all()
    
    if request.method == 'POST':
        try:
            datum_str = request.form.get('datum')
            datum = parse_german_date(datum_str)
            
            betrag_str = request.form.get('betrag').replace(',', '.')
            betrag = Decimal(betrag_str)
            
            beschreibung = request.form.get('beschreibung')
            kategorie = request.form.get('kategorie')
            kostenart = request.form.get('kostenart')
            umlagefaehig = 'umlagefaehig' in request.form
            verteilungsschluessel = request.form.get('verteilungsschluessel', 'Einheiten')
            
            # Miteigentümer nur für Einzahlungen setzen
            miteigentuemer_id = None
            if betrag > 0 and request.form.get('miteigentuemer'):
                miteigentuemer_id = int(request.form.get('miteigentuemer'))
            
            transaktion = Transaktion(
                datum=datum,
                beschreibung=beschreibung,
                kategorie=kategorie,
                kostenart=kostenart,
                betrag=betrag,
                umlagefaehig=umlagefaehig,
                verteilungsschluessel=verteilungsschluessel,
                miteigentuemer_id=miteigentuemer_id,
                jahr=datum.year
            )
            
            db.session.add(transaktion)
            db.session.commit()
            
            # E-Mail-Benachrichtigung senden
            try:
                from utils.email_utils import send_transaction_notification
                admin_users = User.query.filter_by(is_admin=True).all()
                print(f"Admin-Benutzer gefunden: {len(admin_users)}")
                
                for user in admin_users:
                    print(f"Versuche E-Mail zu senden an: {user.username}, E-Mail: {getattr(user, 'email', 'Keine E-Mail')}")
                    if hasattr(user, 'email') and user.email:
                        try:
                            send_transaction_notification(user, transaktion, "hinzugefügt")
                            print(f"E-Mail an {user.email} gesendet")
                        except Exception as mail_error:
                            print(f"Fehler beim Senden der E-Mail an {user.email}: {str(mail_error)}")
                    else:
                        print(f"Benutzer {user.username} hat keine E-Mail-Adresse")
            except Exception as e:
                print(f"Allgemeiner Fehler bei E-Mail-Benachrichtigung: {str(e)}")

            flash('Transaktion erfolgreich hinzugefügt')
            return redirect(url_for('transaktionen.liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen der Transaktion: {str(e)}')
    
    return render_template('transaktionen/neu.html', miteigentuemer=miteigentuemer)

@transaktionen_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Importieren der Daten
            transaktionen, error = importiere_csv(file_path)
            
            if error:
                flash(f'Fehler beim Import: {error}')
                return redirect(request.url)
            
            # Duplikate entfernen, wenn sie bereits in der Datenbank existieren
            imported_count = 0
            duplicate_count = 0
            
            for t in transaktionen:
                # Prüfen, ob die Transaktion bereits existiert
                exists = Transaktion.query.filter(
                    Transaktion.datum == t['datum'],
                    Transaktion.beschreibung == t['beschreibung'],
                    Transaktion.betrag == t['betrag']
                ).first()
                
                if exists:
                    duplicate_count += 1
                    continue  # Überspringen, da Duplikat
                
                # Transaktion erstellen und hinzufügen
                transaktion = Transaktion(
                    datum=t['datum'],
                    beschreibung=t['beschreibung'],
                    kategorie=t['kategorie'],
                    kostenart=t['kostenart'],
                    betrag=t['betrag'],
                    umlagefaehig=t['umlagefaehig'],
                    verteilungsschluessel=t['verteilungsschluessel'],
                    jahr=t['jahr']
                )
                db.session.add(transaktion)
                imported_count += 1
            
            try:
                db.session.commit()
                flash_message = f'{imported_count} Transaktionen erfolgreich importiert.'
                if duplicate_count > 0:
                    flash_message += f' {duplicate_count} Duplikate wurden übersprungen.'
                flash(flash_message)
                return redirect(url_for('transaktionen.liste'))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Speichern in der Datenbank: {str(e)}')
        else:
            flash('Nicht unterstütztes Dateiformat')
    
    return render_template('transaktionen/upload.html')

# Anhang für Transaktionen folgen mit hocladen, view, download und delete
@transaktionen_bp.route('/<int:transaktion_id>/anhang', methods=['GET', 'POST'])
@login_required
def anhang(transaktion_id):
    """
    Zeigt den Anhang einer Transaktion an oder verarbeitet einen neuen Upload
    """
    
    transaktion = Transaktion.query.get_or_404(transaktion_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Keine Datei ausgewählt', 'danger')
            return redirect(request.url)
        
        success, message, _ = save_anhang(file, transaktion_id)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('transaktionen.anhang', transaktion_id=transaktion_id))
    
    return render_template(
        'transaktionen/anhang.html',
        transaktion=transaktion
    )

@transaktionen_bp.route('/<int:transaktion_id>/anhang/view')
@login_required
def view_anhang(transaktion_id):
    """
    Zeigt den Anhang einer Transaktion im Browser an
    """
    transaktion = Transaktion.query.get_or_404(transaktion_id)
    
    if not transaktion.anhang:
        flash('Keine Rechnung für diese Transaktion vorhanden.', 'warning')
        return redirect(url_for('transaktionen.anhang', transaktion_id=transaktion_id))
    
    from flask import send_file
    return send_file(
        transaktion.anhang.get_file_path(),
        download_name=transaktion.anhang.original_dateiname,
        as_attachment=False
    )

@transaktionen_bp.route('/<int:transaktion_id>/anhang/download')
@login_required
def download_anhang(transaktion_id):
    """
    Lädt den Anhang einer Transaktion herunter
    """
    transaktion = Transaktion.query.get_or_404(transaktion_id)
    
    if not transaktion.anhang:
        flash('Keine Rechnung für diese Transaktion vorhanden.', 'warning')
        return redirect(url_for('transaktionen.anhang', transaktion_id=transaktion_id))
    
    from flask import send_file
    return send_file(
        transaktion.anhang.get_file_path(),
        download_name=transaktion.anhang.original_dateiname,
        as_attachment=True
    )

@transaktionen_bp.route('/<int:transaktion_id>/anhang/delete', methods=['POST'])
@login_required
def delete_anhang(transaktion_id):
    """
    Löscht den Anhang einer Transaktion
    """
    
    transaktion = Transaktion.query.get_or_404(transaktion_id)
    
    if not transaktion.anhang:
        flash('Keine Rechnung für diese Transaktion vorhanden.', 'warning')
        return redirect(url_for('transaktionen.anhang', transaktion_id=transaktion_id))
    
    anhang_id = transaktion.anhang.id
    success, message = delete_anhang(anhang_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('transaktionen.anhang', transaktion_id=transaktion_id))

@transaktionen_bp.route('/export', methods=['GET'])
@login_required
def export():
    """
    Exportiert gefilterte Transaktionen als CSV oder Excel
    """
    format = request.args.get('format', 'excel')
    
    # Die gleichen Filter wie bei der liste-Route verwenden
    filter_kostenart = request.args.get('kostenart', session.get('filter_kostenart', ''))
    filter_umlagefaehig = request.args.get('umlagefaehig', session.get('filter_umlagefaehig', ''))
    filter_verteilungsschluessel = request.args.get('verteilungsschluessel', session.get('filter_verteilungsschluessel', ''))
    filter_transaktionstyp = request.args.get('transaktionstyp', session.get('filter_transaktionstyp', ''))
    filter_jahr = request.args.get('jahr', session.get('filter_jahr', datetime.date.today().year), type=int)
    
    # Query erstellen, genau wie bei der liste-Route
    query = Transaktion.query.filter(Transaktion.jahr == filter_jahr)
    
    # Filter für Transaktionstyp (Einzahlungen/Ausgaben)
    if filter_transaktionstyp == 'einzahlungen':
        query = query.filter(Transaktion.betrag > 0)
    elif filter_transaktionstyp == 'ausgaben':
        query = query.filter(Transaktion.betrag < 0)
    
    if filter_kostenart:
        query = query.filter(Transaktion.kostenart == filter_kostenart)
    
    if filter_umlagefaehig:
        umlagefaehig_bool = (filter_umlagefaehig == 'ja')
        query = query.filter(Transaktion.umlagefaehig == umlagefaehig_bool)
    
    if filter_verteilungsschluessel:
        query = query.filter(Transaktion.verteilungsschluessel == filter_verteilungsschluessel)
    
    # Alle gefilterten Transaktionen abrufen
    transaktionen = query.order_by(Transaktion.datum.desc()).all()
    
    # Exportieren
    from utils.export.export import export_transaktionen_as_csv, export_transaktionen_as_excel
    
    if format == 'csv':
        return export_transaktionen_as_csv(transaktionen, filter_jahr)
    else:
        return export_transaktionen_as_excel(transaktionen, filter_jahr)
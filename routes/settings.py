"""
Einstellungen-Blueprint für allgemeine Einstellungen und Verwaltungsfunktionen
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
import os
import datetime
from werkzeug.security import generate_password_hash
from decimal import Decimal
from models import db, User, Transaktion, Miteigentuemer, Wirtschaftsplan, WirtschaftsplanMetadata, Kontostand, RoadmapItem, JahresabschlussKontostand
from services.kategorie_mapping_service import add_mapping, get_all_mappings
from utils.security import admin_required, is_password_strong


# Blueprint initialisieren
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def index():
    """
    Zeigt die Übersicht der Einstellungen an
    """
    return render_template('settings/index.html')

# Benutzerverwaltung
@settings_bp.route('/users')
@login_required
@admin_required
def users_list():
    """
    Zeigt eine Liste aller Benutzer an
    """
    
    users = User.query.all()
    return render_template('settings/users_list.html', users=users)

@settings_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    """Benutzer bearbeiten"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # E-Mail aktualisieren
        email = request.form.get('email')
        if email != user.email:
            # Prüfen, ob die E-Mail bereits verwendet wird
            if email and User.query.filter_by(email=email).first() and user.id != User.query.filter_by(email=email).first().id:
                flash('Diese E-Mail-Adresse wird bereits verwendet.', 'danger')
                return redirect(url_for('settings.user_edit', user_id=user.id))
            
            user.email = email
            user.email_verified = False
            flash('E-Mail-Adresse aktualisiert.', 'success')
        
        # Benachrichtigungseinstellungen aktualisieren
        user.notify_transaction_changes = 'notify_transaction_changes' in request.form
        user.notify_wirtschaftsplan_changes = 'notify_wirtschaftsplan_changes' in request.form
        user.notify_user_changes = 'notify_user_changes' in request.form
        
        # Passwort aktualisieren, wenn angegeben
        if request.form.get('password'):
            password = request.form.get('password')
            
            # Passwort-Stärke prüfen
            if not is_password_strong(password):
                flash('Das Passwort erfüllt nicht die Sicherheitsanforderungen. Es muss mindestens 8 Zeichen lang sein und Groß-/Kleinbuchstaben, Ziffern und Sonderzeichen enthalten.', 'danger')
                return redirect(url_for('settings.user_edit', user_id=user.id))
            
            user.set_password(password)
            flash('Passwort aktualisiert.', 'success')
        
        # Admin-Status aktualisieren
        if current_user.is_admin:
            user.is_admin = 'is_admin' in request.form
        
        db.session.commit()
        flash('Benutzer wurde aktualisiert.', 'success')
        return redirect(url_for('settings.users_list'))
    
    return render_template('settings/user_edit.html', user=user)

@settings_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    """Neuen Benutzer erstellen"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        is_admin = 'is_admin' in request.form
        
        # Prüfen, ob Benutzername bereits existiert
        if User.query.filter_by(username=username).first():
            flash('Dieser Benutzername existiert bereits.', 'danger')
            return redirect(url_for('settings.user_new'))
        
        # Prüfen, ob die E-Mail bereits verwendet wird
        if email and User.query.filter_by(email=email).first():
            flash('Diese E-Mail-Adresse wird bereits verwendet.', 'danger')
            return redirect(url_for('settings.user_new'))
        
        # Passwort-Stärke prüfen
        if not is_password_strong(password):
            flash('Das Passwort erfüllt nicht die Sicherheitsanforderungen. Es muss mindestens 8 Zeichen lang sein und Groß-/Kleinbuchstaben, Ziffern und Sonderzeichen enthalten.', 'danger')
            return redirect(url_for('settings.user_new'))
        
        # Neuen Benutzer erstellen
        user = User(
            username=username,
            is_admin=is_admin,
            email=email,
            email_verified=False,
            notify_transaction_changes='notify_transaction_changes' in request.form,
            notify_wirtschaftsplan_changes='notify_wirtschaftsplan_changes' in request.form,
            notify_user_changes='notify_user_changes' in request.form
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        if email:
            try:
                from utils.email_utils import send_email
                token = user.get_reset_token()  # Gleiche Token-Funktion wie für Passwort-Reset
                # Absolute URL mit BASE_URL erstellen
                verify_url = f"{current_app.config.get('BASE_URL')}{url_for('auth.verify_email_confirm', token=token)}"
        
                result = send_email(
                    subject="[WEG-App] E-Mail-Adresse verifizieren",
                    recipients=[user.email],
                    template='email_verification',
                    user=user,
                    verify_url=verify_url
                )
                
                if result:
                    flash(f'Eine Verifizierungs-E-Mail wurde an {email} gesendet.', 'info')
                else:
                    flash(f'Fehler beim Senden der Verifizierungs-E-Mail an {email}.', 'warning')
            except Exception as e:
                flash(f'Fehler beim Senden der Verifizierungs-E-Mail: {str(e)}', 'warning')

        flash(f'Benutzer "{username}" wurde erstellt.', 'success')
        return redirect(url_for('settings.users_list'))
    
    return render_template('settings/user_new.html')

@settings_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    """
    Löscht einen Benutzer
    """
    if not current_user.is_admin:
        flash("Zugriff verweigert. Sie benötigen Administrator-Rechte.", "error")
        return redirect(url_for('dashboard.index'))
    
    # Verhindern, dass sich ein Admin selbst löscht
    if current_user.id == user_id:
        flash("Sie können sich nicht selbst löschen", "error")
        return redirect(url_for('settings.users_list'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"Benutzer {user.username} erfolgreich gelöscht", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Fehler beim Löschen des Benutzers: {str(e)}", "error")
    
    return redirect(url_for('settings.users_list'))

# In routes/settings.py

@settings_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    """Benutzereinstellungen für E-Mail und Benachrichtigungen"""
    if request.method == 'POST':
        user = current_user
        
        # E-Mail aktualisieren
        new_email = request.form.get('email')
        if new_email != user.email:
            user.email = new_email
            user.email_verified = False  # E-Mail muss neu verifiziert werden
            # Hier könnte ein Verifizierungsprozess gestartet werden
        
        # Benachrichtigungseinstellungen aktualisieren
        user.notify_transaction_changes = 'notify_transaction_changes' in request.form
        user.notify_wirtschaftsplan_changes = 'notify_wirtschaftsplan_changes' in request.form
        user.notify_user_changes = 'notify_user_changes' in request.form
        
        db.session.commit()
        flash('Einstellungen erfolgreich aktualisiert', 'success')
        
    return render_template('settings/preferences.html')

# Datenverwaltung (Löschen von Daten)
@settings_bp.route('/data-management')
@login_required
@admin_required
def data_management():
    """
    Zeigt die Optionen zur Datenverwaltung an
    """
    
    # Verfügbare Jahre für Transaktionen
    transaktionen_jahre = db.session.query(Transaktion.jahr).distinct().order_by(Transaktion.jahr).all()
    transaktionen_jahre = [j[0] for j in transaktionen_jahre]
    
    # Verfügbare Jahre für Wirtschaftsplan
    wirtschaftsplan_jahre = db.session.query(Wirtschaftsplan.jahr).distinct().order_by(Wirtschaftsplan.jahr).all()
    wirtschaftsplan_jahre = [j[0] for j in wirtschaftsplan_jahre]
    
    # Anzahl der Einträge
    stats = {
        'transaktionen_count': Transaktion.query.count(),
        'miteigentuemer_count': Miteigentuemer.query.count(),
        'wirtschaftsplan_count': Wirtschaftsplan.query.count(),
        'user_count': User.query.count()
    }
    
    return render_template(
        'settings/data_management.html', 
        transaktionen_jahre=transaktionen_jahre,
        wirtschaftsplan_jahre=wirtschaftsplan_jahre,
        stats=stats
    )

@settings_bp.route('/delete-data', methods=['POST'])
@login_required
@admin_required
def delete_data():
    """
    Löscht Daten basierend auf den ausgewählten Optionen
    """
    
    data_type = request.form.get('data_type')
    year = request.form.get('year', type=int)
    confirm = request.form.get('confirm') == 'on'
    
    if not confirm:
        flash("Bitte bestätigen Sie den Löschvorgang", "error")
        return redirect(url_for('settings.data_management'))
    
    # Backup erstellen, bevor Daten gelöscht werden
    try:
        if data_type == 'transaktionen' and year:
            # Lösche Transaktionen für ein bestimmtes Jahr
            count = Transaktion.query.filter_by(jahr=year).delete()
            db.session.commit()
            flash(f"{count} Transaktionen für das Jahr {year} wurden gelöscht", "success")
        
        elif data_type == 'transaktionen_all':
            # Lösche alle Transaktionen
            count = Transaktion.query.delete()
            db.session.commit()
            flash(f"{count} Transaktionen wurden gelöscht", "success")
        
        elif data_type == 'wirtschaftsplan' and year:
            # Lösche Wirtschaftsplan für ein bestimmtes Jahr
            count = Wirtschaftsplan.query.filter_by(jahr=year).delete()
            # Auch die Metadaten löschen
            WirtschaftsplanMetadata.query.filter_by(jahr=year).delete()
            db.session.commit()
            flash(f"Wirtschaftsplan für das Jahr {year} wurde gelöscht", "success")
        
        elif data_type == 'wirtschaftsplan_all':
            # Lösche alle Wirtschaftspläne
            count_wp = Wirtschaftsplan.query.delete()
            count_meta = WirtschaftsplanMetadata.query.delete()
            db.session.commit()
            flash(f"{count_wp} Wirtschaftsplaneinträge und {count_meta} Metadaten wurden gelöscht", "success")
        
        else:
            flash("Ungültige Auswahl", "error")
    
    except Exception as e:
        db.session.rollback()
        flash(f"Fehler beim Löschen der Daten: {str(e)}", "error")
    
    return redirect(url_for('settings.data_management'))

# Fügen Sie diese Routen in settings.py hinzu

@settings_bp.route('/kontostand', methods=['GET', 'POST'])
@login_required
@admin_required
def kontostand_manage():
    """
    Kontostände verwalten
    """
    
    from services.kontostand_service import get_current_kontostand, get_kontostand_history, create_kontostand, calculate_theoretical_kontostand
    
    if request.method == 'POST':
        try:
            datum_str = request.form.get('datum')
            datum = datetime.datetime.strptime(datum_str, '%Y-%m-%d').date()
            betrag_str = request.form.get('betrag').replace(',', '.')
            betrag = Decimal(betrag_str)
            kommentar = request.form.get('kommentar', '')
            
            success, message, _ = create_kontostand(
                datum=datum,
                betrag=betrag,
                kommentar=kommentar,
                user_id=current_user.id
            )
            
            if success:
                flash("Kontostand erfolgreich aktualisiert", "success")
            else:
                flash(f"Fehler beim Aktualisieren des Kontostands: {message}", "danger")
            
            return redirect(url_for('settings.kontostand_manage'))
            
        except Exception as e:
            flash(f"Fehler beim Aktualisieren des Kontostands: {str(e)}", "danger")
    
    # Daten für die Anzeige
    aktueller_kontostand = get_current_kontostand()
    kontostände = get_kontostand_history()
    letzter_kontostand = kontostände[0] if kontostände else None
    theoretischer_kontostand = calculate_theoretical_kontostand()
    today = datetime.date.today()
    
    return render_template(
        'settings/kontostand_manage.html',
        aktueller_kontostand=aktueller_kontostand,
        kontostände=kontostände,
        letzter_kontostand=letzter_kontostand,
        theoretischer_kontostand=theoretischer_kontostand,
        today=today
    )

@settings_bp.route('/kontostand/<int:kontostand_id>/delete', methods=['POST'])
@login_required
@admin_required
def kontostand_delete(kontostand_id):
    """
    Löscht einen Kontostand-Eintrag
    """
    
    from services.kontostand_service import delete_kontostand
    
    success, message = delete_kontostand(kontostand_id)
    
    if success:
        flash("Kontostand erfolgreich gelöscht", "success")
    else:
        flash(f"Fehler beim Löschen des Kontostands: {message}", "danger")
    
    return redirect(url_for('settings.kontostand_manage'))

# Ergänzen Sie diese Routen in settings.py

@settings_bp.route('/export', methods=['GET'])
@login_required
def export_view():
    """
    Zeigt die Export-Optionen an
    """
    # Verfügbare Jahre für Transaktionen
    jahre = db.session.query(Transaktion.jahr).distinct().order_by(Transaktion.jahr.desc()).all()
    jahre = [j[0] for j in jahre]
    
    # Anzahl der Transaktionen pro Jahr
    tx_count_by_year = {}
    for jahr in jahre:
        count = Transaktion.query.filter_by(jahr=jahr).count()
        tx_count_by_year[jahr] = count
    
    # Gesamtanzahl der Transaktionen
    tx_total = Transaktion.query.count()
    
    # Verfügbare Jahre für Wirtschaftsplan
    wp_jahre = db.session.query(Wirtschaftsplan.jahr).distinct().order_by(Wirtschaftsplan.jahr.desc()).all()
    wp_jahre = [j[0] for j in wp_jahre]
    
    # Anzahl der Wirtschaftsplan-Einträge pro Jahr
    wp_count_by_year = {}
    for jahr in wp_jahre:
        count = Wirtschaftsplan.query.filter_by(jahr=jahr).count()
        wp_count_by_year[jahr] = count
    
    # Gesamtanzahl der Wirtschaftsplan-Einträge
    wp_total = Wirtschaftsplan.query.count()
    
    # Kontostände
    from services.kontostand_service import get_kontostand_history
    kontostaende = get_kontostand_history()
    
    return render_template(
        'settings/export.html',
        jahre=jahre,
        tx_count_by_year=tx_count_by_year,
        tx_total=tx_total,
        wp_jahre=wp_jahre,
        wp_count_by_year=wp_count_by_year,
        wp_total=wp_total,
        kontostaende=kontostaende
    )

@settings_bp.route('/export/transaktionen', methods=['GET'])
@login_required
def export_transaktionen():
    """
    Exportiert Transaktionen
    """
    from utils.export.export import export_transaktionen_as_csv, export_transaktionen_as_excel
    
    jahr = request.args.get('jahr', type=int)
    format = request.args.get('format', 'csv')
    
    # Transaktionen abfragen
    query = Transaktion.query
    
    if jahr:
        query = query.filter_by(jahr=jahr)
    
    transaktionen = query.order_by(Transaktion.datum.asc()).all()
    
    # Exportieren
    if format == 'excel':
        return export_transaktionen_as_excel(transaktionen, jahr)
    else:
        return export_transaktionen_as_csv(transaktionen, jahr)

@settings_bp.route('/export/kontostaende', methods=['GET'])
@login_required
def export_kontostaende():
    """
    Exportiert Kontostände
    """
    from utils.export.export import export_kontostaende_as_csv
    from services.kontostand_service import get_kontostand_history
    
    kontostaende = get_kontostand_history(limit=0)  # Alle Kontostände
    
    return export_kontostaende_as_csv(kontostaende)

@settings_bp.route('/export/wirtschaftsplan', methods=['GET'])
@login_required
def export_wirtschaftsplan():
    """
    Exportiert Wirtschaftsplan-Einträge
    """
    from utils.export.export import export_wirtschaftsplan_as_csv, export_wirtschaftsplan_as_excel
    
    jahr = request.args.get('jahr', type=int)
    format = request.args.get('format', 'csv')
    
    # Wirtschaftsplan-Einträge abfragen
    query = Wirtschaftsplan.query
    
    if jahr:
        query = query.filter_by(jahr=jahr)
    
    wirtschaftsplan_eintraege = query.order_by(Wirtschaftsplan.kategorie, Wirtschaftsplan.bezeichnung).all()
    
    # Exportieren
    if format == 'excel':
        return export_wirtschaftsplan_as_excel(wirtschaftsplan_eintraege, jahr)
    else:
        return export_wirtschaftsplan_as_csv(wirtschaftsplan_eintraege, jahr)

# Kategorie-Mapping-Routen

@settings_bp.route('/kategorie-mapping', methods=['GET'])
@login_required
@admin_required
def kategorie_mapping():
    """Zeigt die Übersicht der Kategorie-Kostenart-Mappings"""
    
    # Alle eindeutigen Wirtschaftsplan-Kategorien holen
    wp_kategorien = db.session.query(Wirtschaftsplan.kategorie).distinct().all()
    wp_kategorien = sorted([k[0] for k in wp_kategorien if k[0]])
    
    # Alle eindeutigen Transaktions-Kostenarten holen
    tx_kostenarten = db.session.query(Transaktion.kostenart).distinct().all()
    tx_kostenarten = sorted([k[0] for k in tx_kostenarten if k[0]])
    
    # Aktuelle Mappings holen
    mappings = get_all_mappings()
    
    return render_template(
        'settings/kategorie_mapping.html',
        wp_kategorien=wp_kategorien,
        tx_kostenarten=tx_kostenarten,
        mappings=mappings,
        active_tab='kategorie_mapping'
    )

@settings_bp.route('/kategorie-mapping/add', methods=['POST'])
@login_required
@admin_required
def kategorie_mapping_add():
    """Fügt ein neues Mapping hinzu"""

    
    wp_kategorie = request.form.get('wp_kategorie')
    tx_kostenart = request.form.get('tx_kostenart')
    
    if not wp_kategorie or not tx_kostenart:
        flash('Bitte wählen Sie sowohl eine Kategorie als auch eine Kostenart aus.', 'danger')
        return redirect(url_for('settings.kategorie_mapping'))
    
    result = add_mapping(wp_kategorie, tx_kostenart)
    
    if result:
        flash('Zuordnung erfolgreich hinzugefügt.', 'success')
    else:
        flash('Fehler beim Hinzufügen der Zuordnung.', 'danger')
    
    return redirect(url_for('settings.kategorie_mapping'))

@settings_bp.route('/kategorie-mapping/delete', methods=['POST'])
@login_required
@admin_required
def kategorie_mapping_delete():
    """Löscht ein Mapping"""

    
    from services.kategorie_mapping_service import delete_mapping
    
    wp_kategorie = request.form.get('wp_kategorie')
    tx_kostenart = request.form.get('tx_kostenart')
    
    if not wp_kategorie or not tx_kostenart:
        flash('Ungültige Daten.', 'danger')
        return redirect(url_for('settings.kategorie_mapping'))
    
    result = delete_mapping(wp_kategorie, tx_kostenart)
    
    if result:
        flash('Zuordnung erfolgreich gelöscht.', 'success')
    else:
        flash('Fehler beim Löschen der Zuordnung.', 'danger')
    
    return redirect(url_for('settings.kategorie_mapping'))

@settings_bp.route('/systeminfo')
@login_required
def systeminfo():
    """
    Zeigt Systeminformationen an
    """
    from models import Miteigentuemer, Transaktion, Wirtschaftsplan, User, RoadmapItem
    
    # Statistiken aus der Datenbank sammeln
    stats = {
        'miteigentuemer_count': Miteigentuemer.query.count(),
        'transaktionen_count': Transaktion.query.count(),
        'wirtschaftsplan_count': Wirtschaftsplan.query.count(),
        'benutzer_count': User.query.count()
    }
    
    # Roadmap-Daten abrufen und nach Zeitrahmen gruppieren
    roadmap_items = RoadmapItem.query.order_by(RoadmapItem.position).all()
    roadmap = {
        'short_term': [],
        'medium_term': [],
        'long_term': []
    }
    
    for item in roadmap_items:
        roadmap[item.timeframe].append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'status': item.status
        })
    
    return render_template(
        'settings/systeminfo.html',
        miteigentuemer_count=stats['miteigentuemer_count'],
        transaktionen_count=stats['transaktionen_count'],
        wirtschaftsplan_count=stats['wirtschaftsplan_count'],
        benutzer_count=stats['benutzer_count'],
        roadmap=roadmap
    )


# 3. Füge eine neue Route hinzu, um die Roadmap zu aktualisieren

@settings_bp.route('/update_roadmap', methods=['POST'])
@login_required
@admin_required
def update_roadmap():
    """
    Aktualisiert die Roadmap-Einträge
    """
    if not current_user.is_admin:
        flash("Zugriff verweigert. Sie benötigen Administrator-Rechte.", "error")
        return redirect(url_for('dashboard.index'))
    
    try:
        # Bestehende Einträge löschen
        RoadmapItem.query.delete()
        
        # Kurzfristige Ziele
        short_term_items = request.form.to_dict(flat=False)
        for timeframe in ['short_term', 'medium_term', 'long_term']:
            if f'{timeframe}[0][title]' in request.form:
                # Ermittle die Anzahl der Elemente
                i = 0
                while f'{timeframe}[{i}][title]' in request.form:
                    title = request.form.get(f'{timeframe}[{i}][title]')
                    description = request.form.get(f'{timeframe}[{i}][description]', '')
                    status = request.form.get(f'{timeframe}[{i}][status]', 'planned')
                    
                    if title.strip():  # Nur Einträge mit Titel hinzufügen
                        item = RoadmapItem(
                            title=title,
                            description=description,
                            status=status,
                            timeframe=timeframe,
                            position=i
                        )
                        db.session.add(item)
                    
                    i += 1
        
        db.session.commit()
        flash("Roadmap wurde erfolgreich aktualisiert.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Fehler beim Aktualisieren der Roadmap: {str(e)}", "error")
        current_app.logger.error(f"Fehler beim Aktualisieren der Roadmap: {str(e)}")
    
    return redirect(url_for('settings.systeminfo'))

# In routes/settings.py oder einer neuen Datei
@settings_bp.route('/jahresabschluss', methods=['GET'])
@login_required
@admin_required
def jahresabschluss_liste():
    """Zeigt eine Liste aller Jahresabschlüsse"""
    jahresabschluesse = JahresabschlussKontostand.query.order_by(JahresabschlussKontostand.jahr.desc()).all()
    return render_template('settings/jahresabschluss_liste.html', jahresabschluesse=jahresabschluesse)

@settings_bp.route('/jahresabschluss/neu', methods=['GET', 'POST'])
@login_required
@admin_required
def jahresabschluss_neu():
    """Neuen Jahresabschluss erstellen"""
    if request.method == 'POST':
        jahr = request.form.get('jahr', type=int)
        kontostand = request.form.get('kontostand', type=float, default=0.00)
        vorjahres_saldo = request.form.get('vorjahres_saldo', type=float, default=0.00)
        kommentar = request.form.get('kommentar')
        
        # Prüfen, ob für dieses Jahr bereits ein Abschluss existiert
        existing = JahresabschlussKontostand.query.filter_by(jahr=jahr).first()
        if existing:
            flash(f'Für das Jahr {jahr} existiert bereits ein Jahresabschluss', 'danger')
            return redirect(url_for('settings.jahresabschluss_neu'))
        
        jahresabschluss = JahresabschlussKontostand(
            jahr=jahr,
            kontostand=Decimal(str(kontostand)),
            vorjahres_saldo=Decimal(str(vorjahres_saldo)),
            kommentar=kommentar,
            user_id=current_user.id
        )
        
        try:
            db.session.add(jahresabschluss)
            db.session.commit()
            flash(f'Jahresabschluss für {jahr} erfolgreich erstellt', 'success')
            return redirect(url_for('settings.jahresabschluss_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen des Jahresabschlusses: {str(e)}', 'danger')
    
    # Jahre für das Dropdown ermitteln (aktuelle Jahr bis 10 Jahre zurück)
    aktuelles_jahr = datetime.now().year
    jahre = range(aktuelles_jahr - 10, aktuelles_jahr + 1)
    
    return render_template('settings/jahresabschluss_neu.html', jahre=jahre)

@settings_bp.route('/jahresabschluss/<int:jahresabschluss_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def jahresabschluss_bearbeiten(jahresabschluss_id):
    """Jahresabschluss bearbeiten"""
    jahresabschluss = JahresabschlussKontostand.query.get_or_404(jahresabschluss_id)
    
    if request.method == 'POST':
        jahresabschluss.kontostand = Decimal(str(request.form.get('kontostand', type=float, default=0.00)))
        jahresabschluss.vorjahres_saldo = Decimal(str(request.form.get('vorjahres_saldo', type=float, default=0.00)))
        jahresabschluss.kommentar = request.form.get('kommentar')
        jahresabschluss.updated_at = datetime.now()
        
        try:
            db.session.commit()
            flash(f'Jahresabschluss für {jahresabschluss.jahr} erfolgreich aktualisiert', 'success')
            return redirect(url_for('settings.jahresabschluss_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren des Jahresabschlusses: {str(e)}', 'danger')
    
    return render_template('settings/jahresabschluss_bearbeiten.html', jahresabschluss=jahresabschluss)
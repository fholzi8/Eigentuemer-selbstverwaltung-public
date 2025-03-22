"""
Einstellungen-Blueprint für allgemeine Einstellungen und Verwaltungsfunktionen
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
import os
import datetime
from werkzeug.security import generate_password_hash
from decimal import Decimal
from models import db, User, Transaktion, Miteigentuemer, Wirtschaftsplan, WirtschaftsplanMetadata, Kontostand, RoadmapItem, JahresabschlussKontostand, Selbstverwaltung, BriefVorlage, TagesordnungspunktVorlage, WichtigesDokument, KategorieKostenartMapping, LogEntry
from services.kategorie_mapping_service import add_mapping, get_all_mappings
from utils.security import admin_required, is_password_strong
from services.email_config_service import get_all_email_configs, set_email_config, delete_email_config
from services.logging_service import get_logs, log_user_event, log_event, log_error, get_log_retention_days, set_log_retention_days, cleanup_old_logs
from utils.error_handling import handle_db_error
from datetime import datetime, timedelta


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
        # Log-Eintrag erstellen
        log_user_event(
            message=f"{user.username} wurde erfolgreich aktualisiert.",
            affected_user=user,
            user_id=current_user.id
        )
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
        
        # Log-Eintrag erstellen
        log_user_event(
            message=f"{user.username} wurde erfolgreich erstellt.",
            affected_user=user,
            user_id=current_user.id
        )

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
        # Log-Eintrag erstellen
        log_user_event(
            message=f"{user.username} wurde erfolgreich gelöscht.",
            affected_user=user,
            user_id=current_user.id
        )
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

        # Log-Eintrag erstellen
        log_user_event(
            message=f"Benachrichtigungseinstellungen von {user.username} wurde erfolgreich aktualisiert.",
            affected_user=user,
            user_id=current_user.id
        )
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
    
    try:
        if data_type == 'transaktionen' and year:
            # Lösche Transaktionen für ein bestimmtes Jahr
            # Zuerst Anhänge löschen, die zu diesen Transaktionen gehören
            from models import TransaktionAnhang
            
            # Finde alle Transaktions-IDs für das angegebene Jahr
            tx_ids = [tx.id for tx in Transaktion.query.filter_by(jahr=year).all()]
            
            # Lösche alle Anhänge zu diesen Transaktionen
            if tx_ids:
                anhang_count = TransaktionAnhang.query.filter(TransaktionAnhang.transaktion_id.in_(tx_ids)).delete(synchronize_session='fetch')
                print(f"Gelöschte Anhänge: {anhang_count}")
            
            # Lösche die Transaktionen
            tx_count = Transaktion.query.filter_by(jahr=year).delete()
            
            db.session.commit()
            flash(f"{tx_count} Transaktionen für das Jahr {year} wurden gelöscht", "success")
        
        elif data_type == 'transaktionen_all':
            # Lösche alle Transaktionsanhänge
            from models import TransaktionAnhang
            anhang_count = TransaktionAnhang.query.delete()
            
            # Lösche alle Transaktionen
            tx_count = Transaktion.query.delete()
            
            db.session.commit()
            flash(f"{anhang_count} Anhänge und {tx_count} Transaktionen wurden gelöscht", "success")
        
        elif data_type == 'wirtschaftsplan' and year:
            # Lösche Wirtschaftsplan für ein bestimmtes Jahr
            wp_count = Wirtschaftsplan.query.filter_by(jahr=year).delete()
            # Auch die Metadaten löschen
            meta_count = WirtschaftsplanMetadata.query.filter_by(jahr=year).delete()
            
            db.session.commit()
            flash(f"{wp_count} Wirtschaftsplaneinträge und {meta_count} Metadaten für das Jahr {year} wurden gelöscht", "success")
        
        elif data_type == 'wirtschaftsplan_all':
            # Lösche alle Wirtschaftspläne
            wp_count = Wirtschaftsplan.query.delete()
            meta_count = WirtschaftsplanMetadata.query.delete()
            
            db.session.commit()
            flash(f"{wp_count} Wirtschaftsplaneinträge und {meta_count} Metadaten wurden gelöscht", "success")
        
        elif data_type == 'miteigentuemer':
            # Lösche alle Miteigentümer
            # Zuerst alle Transaktionen aktualisieren, die auf Miteigentümer verweisen
            Transaktion.query.update({'miteigentuemer_id': None})
            
            # Jetzt Miteigentümer löschen
            count = Miteigentuemer.query.delete()
            
            db.session.commit()
            flash(f"{count} Miteigentümer wurden gelöscht", "success")
        
        elif data_type == 'kontostaende':
            # Lösche alle Kontostände
            count = Kontostand.query.delete()
            
            db.session.commit()
            flash(f"{count} Kontostände wurden gelöscht", "success")
        
        elif data_type == 'jahresabschluesse':
            # Lösche alle Jahresabschlüsse
            count = JahresabschlussKontostand.query.delete()
            
            db.session.commit()
            flash(f"{count} Jahresabschlüsse wurden gelöscht", "success")
        
        elif data_type == 'vorlagen':
            # Lösche Brief-Vorlagen
            brief_count = BriefVorlage.query.delete()
            # Lösche Tagesordnungspunkte
            top_count = TagesordnungspunktVorlage.query.delete()
            # Lösche Wichtige Dokumente
            dok_count = WichtigesDokument.query.delete()
            
            db.session.commit()
            flash(f"{brief_count} Brief-Vorlagen, {top_count} Tagesordnungspunkte und {dok_count} Dokumente wurden gelöscht", "success")
        
        elif data_type == 'logs':
            # Lösche alle Logs
            count = LogEntry.query.delete()
            
            db.session.commit()
            flash(f"{count} Log-Einträge wurden gelöscht", "success")
        
        elif data_type == 'alles':
            # Lösche ALLE Daten (außer Benutzer!)
            # Es ist wichtig, die Reihenfolge zu beachten, um Fremdschlüssel-Constraints nicht zu verletzen
            
            # 1. Transaktionsanhänge
            from models import TransaktionAnhang
            TransaktionAnhang.query.delete()
            
            # 2. Transaktionen 
            Transaktion.query.delete()
            
            # 3. Wirtschaftspläne und Metadaten
            Wirtschaftsplan.query.delete()
            WirtschaftsplanMetadata.query.delete()
            
            # 4. Miteigentümer
            Miteigentuemer.query.delete()
            
            # 5. Kontostände und Jahresabschlüsse
            Kontostand.query.delete()
            JahresabschlussKontostand.query.delete()
            
            # 6. Vorlagen und Dokumente
            BriefVorlage.query.delete()
            TagesordnungspunktVorlage.query.delete()
            WichtigesDokument.query.delete()
            
            # 7. Mappings und andere Konfigurationen
            KategorieKostenartMapping.query.delete()
            
            # 8. Logs
            LogEntry.query.delete()
            
            # 9. Selbstverwaltungsdaten
            Selbstverwaltung.query.delete()
            
            db.session.commit()
            flash("Alle Daten wurden erfolgreich gelöscht. Benutzerkonten wurden beibehalten.", "success")
        
        else:
            flash("Ungültige Auswahl", "error")
    
    except Exception as e:
        db.session.rollback()
        flash(f"Fehler beim Löschen der Daten: {str(e)}", "error")
    
    return redirect(url_for('settings.data_management'))

# Füge die Routinge für den Kontostand ein 

@settings_bp.route('/kontostand', methods=['GET', 'POST'])
@login_required
@admin_required
def kontostand_manage():
    """
    Kontostände verwalten
    """
    
    from services.kontostand_service import get_current_kontostand, get_kontostand_history, create_kontostand, calculate_theoretical_kontostand
    from datetime import datetime, date
    
    if request.method == 'POST':
        try:
            datum_str = request.form.get('datum')
            # Richtig:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
            # Oder alternativ, falls du date aus datetime importiert hast:
            # datum = date.fromisoformat(datum_str)
            # datum_str = request.form.get('datum')
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
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
    today = date.today()  # Geändert von datetime.date.today()
    
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
    from models import Miteigentuemer, Transaktion, Wirtschaftsplan, User
    import platform
    import flask
    import sys
    import os
    
    # Statistiken aus der Datenbank sammeln
    stats = {
        'miteigentuemer_count': Miteigentuemer.query.count(),
        'transaktionen_count': Transaktion.query.count(),
        'wirtschaftsplan_count': Wirtschaftsplan.query.count(),
        'benutzer_count': User.query.count()
    }
    
    # System-Umgebungsinformationen
    system_info = {
        'os': f"{platform.system()} {platform.release()}",
        'python_version': platform.python_version(),
        'flask_version': flask.__version__,
        'database_type': current_app.config.get('SQLALCHEMY_DATABASE_URI', '').split(':')[0],
        'server': os.environ.get('SERVER_SOFTWARE', 'Waitress' if 'waitress' in sys.modules else 'Flask Development Server')
    }
    
    return render_template(
        'settings/systeminfo.html',
        miteigentuemer_count=stats['miteigentuemer_count'],
        transaktionen_count=stats['transaktionen_count'],
        wirtschaftsplan_count=stats['wirtschaftsplan_count'],
        benutzer_count=stats['benutzer_count'],
        system_info=system_info
    )


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
        # Bestehende Einträge zählen und ausgeben
        existing_items = RoadmapItem.query.all()
        #for item in existing_items:
        #    print(f"  - ID {item.id}: {item.timeframe}, '{item.title}', Status: {item.status}")
        
        # Bestehende Einträge löschen
        delete_result = RoadmapItem.query.delete()
        
        # Neue Einträge zählen
        new_items_count = 0
        new_items = []  # Für Logging-Zwecke
        
        # Timeframes und alle möglichen Formular-Feldnamen
        timeframes_mapping = {
            'short_term': ['short_term', 'shortTerm'],
            'medium_term': ['medium_term', 'mediumTerm'],
            'long_term': ['long_term', 'longTerm']
        }
        
        # Timeframes durchgehen
        for db_timeframe, field_names in timeframes_mapping.items():
            timeframe_count = 0
            
            # Verschiedene mögliche Feldnamen-Formate durchgehen
            for field_name in field_names:
                i = 0
                # Durchlaufe alle möglichen Indices bis wir keinen Titel mehr finden
                while True:
                    title_key = f"{field_name}[{i}][title]"
                    
                    if title_key in request.form:
                        title = request.form.get(title_key, '').strip()
                        description = request.form.get(f"{field_name}[{i}][description]", '')
                        status = request.form.get(f"{field_name}[{i}][status]", 'planned')
                        
                        if title:
                            item = RoadmapItem(
                                title=title,
                                description=description,
                                status=status,
                                timeframe=db_timeframe,
                                position=i
                            )
                            db.session.add(item)
                            new_items.append({
                                'timeframe': db_timeframe,
                                'title': title,
                                'status': status
                            })
                            timeframe_count += 1
                            new_items_count += 1
                            #print(f"  ✓ Eintrag hinzugefügt: {db_timeframe}[{i}] - Titel: '{title}', Status: '{status}'")
                    else:
                        break  # Wenn ein Index nicht gefunden wird, brechen wir für dieses Feldnamen-Format ab
                    
                    i += 1
                    # Vorsichtshalber eine Grenze setzen
                    if i >= 50:
                        break
        
        # Änderungen speichern
        db.session.commit()
        
        # Log-Eintrag erstellen
        from services.logging_service import log_event
        log_event(
            category='system',
            level='info',
            message=f"Roadmap erfolgreich aktualisiert mit {new_items_count} Einträgen",
            details={
                'roadmap_items': new_items,
                'user': current_user.username
            },
            user_id=current_user.id
        )
        
        # Ergebnis verifizieren
        final_items = RoadmapItem.query.all()
        
        #flash(f"Roadmap wurde erfolgreich aktualisiert. {new_items_count} Einträge gespeichert.", "success")
    except Exception as e:
        db.session.rollback()
        # Fehler loggen
        from services.logging_service import log_error
        from utils.error_handling import handle_db_error  # Dieser Import fehlt in deinem Code
        
        log_error(
            message=f"Fehler beim Aktualisieren der Roadmap: {str(e)}",
            exception=e,
            user_id=current_user.id,
            details={'form_data': dict(request.form)}
        )
        
        handle_db_error(e, "Roadmap aktualisieren", current_user.id, {
            'form_data': dict(request.form)
        })
        
        current_app.logger.error(f"Fehler beim Aktualisieren der Roadmap: {str(e)}")
        flash(f"Fehler beim Aktualisieren der Roadmap: {str(e)}", "error")
    
    return redirect(url_for('settings.roadmap_view'))


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
    
    # Jahre für das Dropdown ermitteln (aktuelle Jahr bis 3 Jahre zurück)
    from datetime import datetime
    aktuelles_jahr = datetime.now().year
    jahre = range(aktuelles_jahr - 3, aktuelles_jahr + 1)
    
    return render_template('settings/jahresabschluss_neu.html', jahre=jahre)

@settings_bp.route('/jahresabschluss/<int:jahresabschluss_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def jahresabschluss_bearbeiten(jahresabschluss_id):
    """Jahresabschluss bearbeiten"""
    jahresabschluss = JahresabschlussKontostand.query.get_or_404(jahresabschluss_id)
    
    if request.method == 'POST':
        from datetime import datetime
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

@settings_bp.route('/jahresabschluss/delete/<int:jahresabschluss_id>', methods=['POST'])
@login_required
@admin_required
def jahresabschluss_delete(jahresabschluss_id):
    """Jahresabschluss löschen"""
    jahresabschluss = JahresabschlussKontostand.query.get_or_404(jahresabschluss_id)
    
    try:
        db.session.delete(jahresabschluss)
        db.session.commit()
        flash(f'Jahresabschluss für {jahresabschluss.jahr} erfolgreich gelöscht', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Löschen des Jahresabschlusses: {str(e)}', 'danger')
        
    return redirect(url_for('settings.jahresabschluss_liste'))


@settings_bp.route('/email-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def email_settings():
    """Zeigt und verwaltet E-Mail-Einstellungen"""
    
    if request.method == 'POST':
        if 'save_config' in request.form:
            # E-Mail-Konfiguration speichern
            key = request.form.get('key')
            value = request.form.get('value')
            description = request.form.get('description')
            
            if not key or not value:
                flash('Bitte geben Sie einen Schlüssel und einen Wert an.', 'danger')
                return redirect(url_for('settings.email_settings'))
            
            result = set_email_config(key, value, description)
            
            if result:
                flash('E-Mail-Konfiguration erfolgreich gespeichert.', 'success')
            else:
                flash('Fehler beim Speichern der E-Mail-Konfiguration.', 'danger')
            
            return redirect(url_for('settings.email_settings'))
        
        elif 'delete_config' in request.form:
            # E-Mail-Konfiguration löschen
            key = request.form.get('key')
            
            if not key:
                flash('Ungültiger Schlüssel.', 'danger')
                return redirect(url_for('settings.email_settings'))
            
            result = delete_email_config(key)
            
            if result:
                flash('E-Mail-Konfiguration erfolgreich gelöscht.', 'success')
            else:
                flash('Fehler beim Löschen der E-Mail-Konfiguration.', 'danger')
            
            return redirect(url_for('settings.email_settings'))
    
    # Alle Konfigurationen abrufen
    email_configs = get_all_email_configs()
    
    return render_template(
        'settings/email_settings.html',
        email_configs=email_configs,
        active_tab='email_settings'
    )

@settings_bp.route('/test-email-connection', methods=['GET', 'POST'])
@login_required
@admin_required
def test_email_connection():
    from services.email_config_service import diagnose_email_settings
    from utils.email_utils import test_smtp_connection, send_test_email
    
    result = {'success': False, 'message': ''}
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'diagnose':
            # E-Mail-Einstellungen diagnostizieren
            diagnose_email_settings()
            result['success'] = True
            result['message'] = 'E-Mail-Einstellungen wurden ausgegeben. Bitte überprüfe die Konsole/Log-Datei.'
        
        elif action == 'test_connection':
            # SMTP-Verbindung testen
            success = test_smtp_connection()
            result['success'] = success
            result['message'] = 'SMTP-Verbindungstest erfolgreich.' if success else 'SMTP-Verbindungstest fehlgeschlagen. Bitte überprüfe die Konsole/Log-Datei für Details.'
        
        elif action == 'send_test':
            # Test-E-Mail senden
            recipient = request.form.get('recipient')
            if not recipient:
                result['message'] = 'Bitte gib eine E-Mail-Adresse an.'
            else:
                success = send_test_email(recipient)
                result['success'] = success
                result['message'] = f'Test-E-Mail wurde an {recipient} gesendet.' if success else f'Fehler beim Senden der Test-E-Mail an {recipient}.'
    
    return render_template('settings/test_email.html', result=result)

@settings_bp.route('/parameter-settings')
@login_required
@admin_required
def parameter_settings():
    """Zeigt die Übersicht der Parametereinstellungen an"""
    return render_template('settings/parameter_settings.html')


@settings_bp.route('/logs', methods=['GET'])
@login_required
@admin_required
def logs_view():
    # Automatische Log-Bereinigung bei Bedarf durchführen
    #schedule_log_cleanup()

    """Zeigt die Log-Einträge an"""
    
    # Filter aus Request-Parametern
    category = request.args.get('category')
    level = request.args.get('level')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Datumsfilter
    days = request.args.get('days', 7, type=int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Offset für Paginierung
    offset = (page - 1) * per_page
    
    # Logs abrufen
    logs, total_count = get_logs(
        category=category, 
        level=level, 
        limit=per_page, 
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )
    
    # Paginierungsinformationen
    pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < pages
    
    # Benutzer für die Anzeige laden
    user_ids = set(log.user_id for log in logs if log.user_id is not None)
    users = {user.id: user.username for user in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
    
    return render_template(
        'settings/logs.html',
        logs=logs,
        users=users,
        category=category,
        level=level,
        days=days,
        page=page,
        pages=pages,
        has_prev=has_prev,
        has_next=has_next,
        total_count=total_count
    )

@settings_bp.route('/roadmap')
@login_required
def roadmap_view():
    """
    Zeigt die Roadmap-Ansicht
    """
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
    
    return render_template('settings/roadmap.html', roadmap=roadmap)

@settings_bp.route('/log-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def log_settings():
    """Einstellungen für den Log-Viewer"""
    
    if request.method == 'POST':
        retention_days = request.form.get('retention_days', type=int)
        if retention_days is not None and retention_days > 0:
            set_log_retention_days(retention_days)
            
            # Wenn "cleanup_now" ausgewählt wurde, alte Logs sofort bereinigen
            if 'cleanup_now' in request.form:
                deleted_count = cleanup_old_logs()
                flash(f'{deleted_count} alte Log-Einträge wurden gelöscht.', 'success')
            else:
                flash('Log-Aufbewahrungsdauer erfolgreich aktualisiert.', 'success')
        else:
            flash('Bitte geben Sie eine gültige Anzahl von Tagen ein.', 'danger')
        
        return redirect(url_for('settings.log_settings'))
    
    # Aktuelle Einstellung laden
    retention_days = get_log_retention_days()
    
    return render_template('settings/log_settings.html', retention_days=retention_days)

@settings_bp.route('/selbstverwaltung', methods=['GET', 'POST'])
@login_required
@admin_required
def selbstverwaltung():
    """
    Zeigt und verwaltet die Daten der Selbstverwaltung
    """
    # Daten abrufen oder neuen Eintrag erstellen
    daten = Selbstverwaltung.query.first()
    if daten is None:
        daten = Selbstverwaltung(
            name="",
            adresse="",
            plz="",
            ort="",
            land="Deutschland",
            verwalter="",
            email="",
            telefon=""
        )
        db.session.add(daten)
        db.session.commit()
    
    if request.method == 'POST':
        # Pflichtfelder
        daten.name = request.form.get('name')
        daten.adresse = request.form.get('adresse')
        daten.plz = request.form.get('plz')
        daten.ort = request.form.get('ort')
        daten.land = request.form.get('land')
        daten.verwalter = request.form.get('verwalter')
        daten.email = request.form.get('email')
        daten.telefon = request.form.get('telefon')
        
        # Optionale Felder
        daten.beisitzer = request.form.get('beisitzer')
        daten.beisitzer_kontakt = request.form.get('beisitzer_kontakt')
        daten.beirat_vorsitz = request.form.get('beirat_vorsitz')
        daten.beirat_vorsitz_kontakt = request.form.get('beirat_vorsitz_kontakt')
        daten.beirat_mitglieder = request.form.get('beirat_mitglieder')
        daten.beirat_mitglieder_kontakt = request.form.get('beirat_mitglieder_kontakt')
        daten.steuernummer = request.form.get('steuernummer')
        
        try:
            db.session.commit()
            flash('Daten der Selbstverwaltung erfolgreich aktualisiert', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern der Daten: {str(e)}', 'danger')
        
        return redirect(url_for('settings.selbstverwaltung'))
    
    return render_template('settings/selbstverwaltung.html', daten=daten)
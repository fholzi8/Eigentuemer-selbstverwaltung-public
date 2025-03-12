"""
Authentication-Blueprint für Login/Logout-Funktionalität
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

from models import db, User
from utils.email_utils import send_password_reset_email, send_test_email, send_email
from utils.security import is_password_strong
from services.logging_service import log_user_event, log_error

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Wenn der Benutzer noch keinen Argon2-Hash hat, migriere ihn
            if not user.password_hash.startswith('$argon2'):
                user.set_password(password)  # Setzt ein neues Argon2-Hash
                db.session.commit()

                # Log-Eintrag erstellen
                log_user_event(
                    message=f"Passwort von {user.username} wurde erfolgreich mit Argon2-Hash gesetzt.",
                    affected_user=user,
                    user_id=current_user.id
                )
                
            # Letztes Login aktualisieren, falls das Feld existiert
            if hasattr(user, 'last_login'):
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log-Eintrag erstellen
                log_user_event(
                    message=f"Passwort von {user.username} wurde erfolgreich mit Hash gesetzt.",
                    affected_user=user,
                    user_id=current_user.id
                )

            login_user(user)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Ungültiger Benutzername oder Passwort', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        # Immer eine positive Antwort geben, um E-Mail-Enumeration zu verhindern
        flash('Eine E-Mail mit Anweisungen zum Zurücksetzen des Passworts wurde gesendet, falls ein Konto mit dieser E-Mail-Adresse existiert.', 'info')
        
        if user:
            result = send_password_reset_email(user)
            if not result:
                logger.warning(f"Fehler beim Senden der Passwort-Reset-E-Mail an {email}")
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_request.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('Der Token ist ungültig oder abgelaufen.', 'warning')
        return redirect(url_for('auth.request_reset'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Die Passwörter stimmen nicht überein.', 'danger')
            return render_template('auth/reset_password.html')
        
        # Hier kannst du die is_password_strong Funktion verwenden
        if not is_password_strong(password):
            flash('Das Passwort erfüllt nicht die Sicherheitsanforderungen.', 'danger')
            return render_template('auth/reset_password.html')
        
        user.set_password(password)
        db.session.commit()
        
        # Log-Eintrag erstellen
        log_user_event(
            message=f"Passwort des {user.username} wurde erfolgreich zurückgesetzt.",
            affected_user=user,
            user_id=current_user.id
        )
        flash('Ihr Passwort wurde erfolgreich zurückgesetzt. Sie können sich jetzt anmelden.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Benutzerprofilseite mit E-Mail-Verwaltung"""
    if request.method == 'POST':
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # E-Mail aktualisieren
        if email and email != current_user.email:
            # Prüfen, ob die E-Mail bereits verwendet wird
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Diese E-Mail-Adresse wird bereits verwendet.', 'danger')
            else:
                current_user.email = email
                current_user.email_verified = False
                flash('Ihre E-Mail-Adresse wurde aktualisiert. Bitte verifizieren Sie Ihre neue E-Mail-Adresse.', 'success')
        
        # Benachrichtigungseinstellungen aktualisieren
        if 'notify_transaction_changes' in request.form:
            current_user.notify_transaction_changes = True
        else:
            current_user.notify_transaction_changes = False
            
        if 'notify_wirtschaftsplan_changes' in request.form:
            current_user.notify_wirtschaftsplan_changes = True
        else:
            current_user.notify_wirtschaftsplan_changes = False
            
        if 'notify_user_changes' in request.form:
            current_user.notify_user_changes = True
        else:
            current_user.notify_user_changes = False
        
        # Passwort ändern
        if new_password:
            if not current_password:
                flash('Bitte geben Sie Ihr aktuelles Passwort ein, um es zu ändern.', 'danger')
            elif not current_user.check_password(current_password):
                flash('Das aktuelle Passwort ist nicht korrekt.', 'danger')
            elif new_password != confirm_password:
                flash('Die neuen Passwörter stimmen nicht überein.', 'danger')
            elif not is_password_strong(new_password):
                flash('Das neue Passwort erfüllt nicht die Sicherheitsanforderungen.', 'danger')
            else:
                current_user.set_password(new_password)
                flash('Ihr Passwort wurde aktualisiert.', 'success')
        
        db.session.commit()

        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html')

@auth_bp.route('/verify_email')
@login_required
def send_verification_email():
    """Sendet eine E-Mail-Verifizierungs-E-Mail"""
    if not current_user.email:
        flash('Sie haben keine E-Mail-Adresse hinterlegt.', 'warning')
        return redirect(url_for('auth.profile'))
    
    if current_user.email_verified:
        flash('Ihre E-Mail-Adresse ist bereits verifiziert.', 'info')
        return redirect(url_for('auth.profile'))
    
    # Token generieren und E-Mail senden
    token = current_user.get_reset_token()
    # Absolute URL mit BASE_URL erstellen
    verify_url = f"{current_app.config.get('BASE_URL')}{url_for('auth.verify_email_confirm', token=token)}"
    
    
    result = send_email(
        subject="[WEG-App] E-Mail-Adresse verifizieren",
        recipients=[current_user.email],
        template='email_verification',
        user=current_user,
        verify_url=verify_url
    )
    
    if result:
        flash('Eine Verifizierungs-E-Mail wurde an Ihre E-Mail-Adresse gesendet.', 'success')
    else:
        flash('Fehler beim Senden der Verifizierungs-E-Mail.', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/verify_email/<token>')
def verify_email_confirm(token):
    """Bestätigt eine E-Mail-Adresse mit Token"""
    if current_user.is_authenticated and current_user.email_verified:
        flash('Ihre E-Mail-Adresse ist bereits verifiziert.', 'info')
        return redirect(url_for('auth.profile'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('Der Verifizierungslink ist ungültig oder abgelaufen.', 'warning')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    db.session.commit()
    
    if current_user.is_authenticated:
        flash('Ihre E-Mail-Adresse wurde erfolgreich verifiziert.', 'success')
        return redirect(url_for('auth.profile'))
    else:
        flash('Ihre E-Mail-Adresse wurde erfolgreich verifiziert. Sie können sich jetzt anmelden.', 'success')
        return redirect(url_for('auth.login'))

@auth_bp.route('/test_email')
@login_required
def test_email():
    """Sendet eine Test-E-Mail (nur für Administratoren)"""
    if not current_user.is_admin:
        flash('Nur Administratoren können Test-E-Mails senden.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if not current_user.email:
        flash('Sie haben keine E-Mail-Adresse hinterlegt.', 'warning')
        return redirect(url_for('auth.profile'))
    
    result = send_test_email(current_user.email)
    
    if result:
        flash(f'Eine Test-E-Mail wurde an {current_user.email} gesendet.', 'success')
    else:
        flash('Fehler beim Senden der Test-E-Mail.', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/direct_test_email')
@login_required
def direct_test_email():
    """Sendet eine Test-E-Mail direkt ohne Templates"""
    if not current_user.is_admin:
        flash('Nur Administratoren können Test-E-Mails senden.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if not current_user.email:
        flash('Sie haben keine E-Mail-Adresse hinterlegt.', 'warning')
        return redirect(url_for('auth.profile'))
    
    try:
        from flask_mail import Message
        
        print(f"Versuche direkte E-Mail zu senden an: {current_user.email}")
        
        # Ähnlich wie in deinem Test-Skript
        msg = Message("WEG-App: Direkte Test-E-Mail",
                     recipients=[current_user.email])
        
        msg.body = "Dies ist eine direkte Test-E-Mail ohne Templates."
        msg.html = "<h1>Test</h1><p>Dies ist eine direkte Test-E-Mail ohne Templates.</p>"
        
        from extensions import mail
        mail.send(msg)  # Direkt senden (nicht asynchron)
        
        print("E-Mail wurde direkt gesendet!")
        flash(f'Eine direkte Test-E-Mail wurde an {current_user.email} gesendet.', 'success')
    except Exception as e:
        print(f"Fehler beim direkten E-Mail-Versand: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Fehler beim Senden der direkten Test-E-Mail: {str(e)}', 'danger')
    
    return redirect(url_for('auth.profile'))
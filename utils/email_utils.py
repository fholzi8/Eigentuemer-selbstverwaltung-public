"""
Funktionen für den E-Mail-Versand

"""

from flask import current_app, render_template, url_for
from flask_mail import Message
from threading import Thread
from extensions import mail

def send_async_email(app, msg):
    """Sendet eine E-Mail asynchron in einem Thread"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, template, sender=None, cc=None, **kwargs):
    """
    Sendet eine E-Mail mit HTML und Text-Version
    """
    try:
        app = current_app._get_current_object()
        
        print(f"Beginne E-Mail-Versand: {subject} an {recipients}")

        # Standard-E-Mail-Adresse
        if sender is None:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            
        msg = Message(subject, sender=sender, recipients=recipients)
        
        if cc:
            msg.cc = cc
        
        # Text-Version
        try:
            print(f"Versuche Template zu rendern: emails/{template}.txt")
            msg.body = render_template(f'emails/{template}.txt', **kwargs)
        except Exception as template_err:
            print(f"Fehler beim Rendern der Text-Vorlage: {template_err}")
            msg.body = f"Inhalt konnte nicht generiert werden. Bitte kontaktieren Sie den Administrator."
        
        # HTML-Version
        try:
            print(f"Versuche Template zu rendern: emails/{template}.html")
            msg.html = render_template(f'emails/{template}.html', **kwargs)
        except Exception as template_err:
            print(f"Fehler beim Rendern der HTML-Vorlage: {template_err}")
            if msg.body:
                msg.html = f"<html><body><pre>{msg.body}</pre></body></html>"
        
        # Asynchrones Senden
        Thread(target=send_async_email, args=(app, msg)).start()
        print(f"E-Mail-Versand gestartet: {subject} an {recipients}")
        return True
    except Exception as e:
        print(f"Fehler beim Erstellen der E-Mail: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Spezifische E-Mail-Funktionen

def send_transaction_notification(user, transaction, action):
    """Benachrichtigung bei Transaktionsänderungen"""
    try:
        if not hasattr(user, 'email') or not user.email:
            print(f"Benutzer {user.username} hat keine E-Mail-Adresse")
            return
        
        if hasattr(user, 'email_verified') and not user.email_verified:
            print(f"E-Mail von Benutzer {user.username} nicht verifiziert")
            return
            
        if hasattr(user, 'notify_transaction_changes') and not user.notify_transaction_changes:
            print(f"Benutzer {user.username} hat Transaktionsbenachrichtigungen deaktiviert")
            return
        
        subject = f"[WEG-App] Transaktion {action}"
        recipients = [user.email]
        
        # Optional: CC an das WEG-Archiv
        cc = [current_app.config.get('WEG_ARCHIVE_EMAIL')] if current_app.config.get('WEG_ARCHIVE_EMAIL') else None
        
        print(f"Sende E-Mail an: {recipients}, CC: {cc}")
        send_email(
            subject=subject,
            recipients=recipients,
            cc=cc,
            template='transaction_notification',
            sender=current_app.config.get('MAIL_NOTIFICATION_SENDER'),
            user=user,
            transaction=transaction,
            action=action
        )
        print(f"E-Mail erfolgreich gesendet an: {recipients}")
        return True
    except Exception as e:
        print(f"Fehler beim Senden der Transaktionsbenachrichtigung: {str(e)}")
        return False

def send_password_reset_email(user):
    """Sendet eine E-Mail zum Zurücksetzen des Passworts"""
    if not user.email or not user.email_verified:
        print(f"Benutzer {user.username} hat keine E-Mail-Adresse")
        return False
    
    try:
        token = user.get_reset_token()
        print(f"Sende Passwort-Reset-E-Mail an {user.email}")
        
        reset_url = f"{current_app.config.get('BASE_URL')}{url_for('auth.reset_password', token=token)}"
        
        return send_email(
            subject="[WEG-App] Passwort zurücksetzen",
            recipients=[user.email],
            template='password_reset',
            user=user,
            token=token,
            reset_url=reset_url
        )
    except Exception as e:
        print(f"Fehler beim Senden der Passwort-Reset-E-Mail: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_wirtschaftsplan_notification(user, wirtschaftsplan, action):
    """Benachrichtigung bei Wirtschaftsplanänderungen"""
    if not user.email or not user.email_verified or not user.notify_wirtschaftsplan_changes:
        return
    
    subject = f"[WEG-App] Wirtschaftsplan {action}"
    send_email(
        subject=subject,
        recipients=[user.email],
        template='wirtschaftsplan_notification',
        user=user,
        wirtschaftsplan=wirtschaftsplan,
        action=action
    )

def send_user_notification(admin, affected_user, action):
    """Benachrichtigung bei Benutzeränderungen"""
    if not admin.email: # or not admin.email_verified or not admin.notify_user_changes:
        return
    
    subject = f"[WEG-App] Benutzer {action}"
    send_email(
        subject=subject,
        recipients=[admin.email],
        template='user_notification',
        admin=admin,
        affected_user=affected_user,
        action=action
    )
def send_test_email(recipient, sender=None):
    """
    Sendet eine Test-E-Mail
    
    Args:
        recipient (str): E-Mail-Empfänger
        sender (str, optional): E-Mail-Absender
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        app = current_app._get_current_object()
        
        if sender is None:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            
        msg = Message("WEG-App: Test-E-Mail", sender=sender, recipients=[recipient])
        
        # Text-Version
        msg.body = """
        Dies ist eine Test-E-Mail der WEG-Abrechnungsanwendung.
        
        Wenn Sie diese E-Mail erhalten, funktioniert der E-Mail-Versand korrekt.
        
        Mit freundlichen Grüßen
        Ihr WEG-App-Team
        """
        
        # HTML-Version
        msg.html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
                .content { padding: 20px 0; }
                .footer { font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>WEG-App: Test-E-Mail</h2>
                </div>
                <div class="content">
                    <p>Dies ist eine Test-E-Mail der WEG-Abrechnungsanwendung.</p>
                    <p>Wenn Sie diese E-Mail erhalten, funktioniert der E-Mail-Versand korrekt.</p>
                </div>
                <div class="footer">
                    <p>Mit freundlichen Grüßen<br>Ihr WEG-App-Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Asynchrones Senden
        Thread(target=send_async_email, args=(app, msg)).start()
        return True
    except Exception as e:
        print(f"Fehler beim Senden der Test-E-Mail: {e}")
        return False
    
def test_smtp_connection(use_config=True, manual_settings=None):
    """
    Testet die SMTP-Verbindung direkt
    
    Args:
        use_config (bool): Wenn True, werden die Einstellungen aus der App-Konfiguration verwendet
        manual_settings (dict, optional): Manuelle Einstellungen für den Test
            {
                'server': 'smtp.example.com',
                'port': 465,
                'use_ssl': True,
                'use_tls': False,
                'username': 'user@example.com',
                'password': 'password',
                'test_recipient': 'recipient@example.com'
            }
    
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    import smtplib
    from email.mime.text import MIMEText
    
    try:
        app = current_app._get_current_object()
        
        if use_config:
            # Konfiguration aus der App holen
            server = app.config.get('MAIL_SERVER')
            port = app.config.get('MAIL_PORT')
            use_ssl = app.config.get('MAIL_USE_SSL', False)
            use_tls = app.config.get('MAIL_USE_TLS', False)
            username = app.config.get('MAIL_USERNAME')
            password = app.config.get('MAIL_PASSWORD')
            test_recipient = app.config.get('MAIL_USERNAME')  # Standardmäßig an sich selbst senden
        else:
            # Manuelle Einstellungen verwenden
            if not manual_settings:
                raise ValueError("Wenn use_config=False, muss manual_settings angegeben werden")
            
            server = manual_settings.get('server')
            port = manual_settings.get('port')
            use_ssl = manual_settings.get('use_ssl', False)
            use_tls = manual_settings.get('use_tls', False)
            username = manual_settings.get('username')
            password = manual_settings.get('password')
            test_recipient = manual_settings.get('test_recipient', username)
        
        print(f"\n=== SMTP-Verbindungstest ===")
        print(f"Server: {server}")
        print(f"Port: {port}")
        print(f"SSL: {use_ssl}")
        print(f"TLS: {use_tls}")
        print(f"Benutzername: {username}")
        print(f"Passwort: {'Gesetzt' if password else 'Nicht gesetzt'}")
        
        # SMTP-Verbindung herstellen
        print("\nVerbindung wird hergestellt...")
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)
            if use_tls:
                print("Starte TLS...")
                smtp.starttls()
        
        # Verbindungsdetails ausgeben
        print(f"Verbunden mit {server}:{port}")
        
        # Login
        if username and password:
            print(f"Anmeldung mit Benutzername: {username}")
            smtp.login(username, password)
            print("Anmeldung erfolgreich")
        
        # Test-E-Mail senden
        if test_recipient:
            msg = MIMEText("Dies ist eine Test-E-Mail von der WEG-App. SMTP-Verbindungstest.")
            msg['Subject'] = "WEG-App: SMTP-Test"
            msg['From'] = username
            msg['To'] = test_recipient
            
            print(f"Sende Test-E-Mail an {test_recipient}...")
            smtp.send_message(msg)
            print("Test-E-Mail gesendet")
        
        smtp.quit()
        print("Verbindung geschlossen")
        print("\nTest erfolgreich! SMTP-Verbindung funktioniert.")
        return True
    except Exception as e:
        print(f"\nFehler bei SMTP-Test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
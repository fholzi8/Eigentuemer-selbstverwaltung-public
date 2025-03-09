"""
E-Mail-Funktionen für die WEG-Abrechnung Anwendung
"""

from flask import current_app, render_template
from flask_mail import Message
from extensions import mail

def send_email(subject, recipients, text_body, html_body=None, attachments=None, sender=None):
    """
    Sendet eine E-Mail
    
    Args:
        subject (str): Betreff der E-Mail
        recipients (list): Liste der Empfänger
        text_body (str): Text-Version der E-Mail
        html_body (str, optional): HTML-Version der E-Mail. Defaults to None.
        attachments (list, optional): Liste der Anhänge (Tuples von (Dateiname, MIME-Typ, Datei-Inhalt)). Defaults to None.
        sender (str, optional): Absender der E-Mail. Defaults to None (verwendet Standard-Absender).
    """
    sender = sender or current_app.config['MAIL_DEFAULT_SENDER']
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    if attachments:
        for attachment in attachments:
            if len(attachment) == 3:
                filename, mime_type, data = attachment
                msg.attach(filename=filename, content_type=mime_type, data=data)
    
    mail.send(msg)

def send_password_reset_email(user):
    """
    Sendet eine E-Mail zum Zurücksetzen des Passworts
    
    Args:
        user (User): Benutzer, für den das Passwort zurückgesetzt werden soll
    """
    token = user.get_reset_password_token()
    send_email(
        '[WEG-Abrechnung] Passwort zurücksetzen',
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )
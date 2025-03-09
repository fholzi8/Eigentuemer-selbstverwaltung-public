# In utils/security.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    Decorator, der prüft, ob ein Benutzer Administrator-Rechte hat.
    Wenn nicht, wird eine Fehlermeldung angezeigt und zur Dashboard-Seite umgeleitet.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Zugriff verweigert. Sie benötigen Administrator-Rechte.", "error")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
def is_password_strong(password):
    """
    Überprüft, ob ein Passwort den Sicherheitsanforderungen entspricht.
    
    - Mindestens 8 Zeichen
    - Mindestens 1 Großbuchstabe
    - Mindestens 1 Kleinbuchstabe
    - Mindestens 1 Ziffer
    - Mindestens 1 Sonderzeichen
    """
    if len(password) < 8:
        return False
    
    if not any(c.isupper() for c in password):
        return False
    
    if not any(c.islower() for c in password):
        return False
    
    if not any(c.isdigit() for c in password):
        return False
    
    # Überprüfe auf Sonderzeichen
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
    if not any(c in special_chars for c in password):
        return False
    
    return True
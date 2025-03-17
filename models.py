"""
Datenbankmodelle für die WEG-Abrechnung Anwendung
"""

import datetime
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from decimal import Decimal
import os
from werkzeug.utils import secure_filename



# Instanz des PasswordHasher erstellen
ph = PasswordHasher()

# Datenbank initialisieren
db = SQLAlchemy()

# Datenmodelle definieren

# Klasse für User mit Passwort Reset und Email-Verifizierung
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    #def set_password(self, password):
    #   self.password_hash = generate_password_hash(password)

    # def check_password(self, password):
    #    return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Setzt das Passwort mit Argon2-Hashing"""
        try:
            self.password_hash = ph.hash(password)
        except Exception as e:
            # Fallback zur alten Methode, falls Argon2 fehlschlägt
            self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Überprüft das Passwort mit Fallback zur alten Methode"""
        # Prüfe, ob es ein Argon2-Hash ist
        if self.password_hash and self.password_hash.startswith('$argon2'):
            try:
                # Argon2 Verifizierung versuchen
                ph.verify(self.password_hash, password)
                
                # Rehashing, falls nötig
                if ph.check_needs_rehash(self.password_hash):
                    self.password_hash = ph.hash(password)
                    db.session.add(self)
                    db.session.commit()
                return True
            except (VerifyMismatchError, InvalidHashError):
                return False
        else:
            # Alte Methode als Fallback
            return check_password_hash(self.password_hash, password)


    email = db.Column(db.String(120), unique=True, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Benachrichtigungseinstellungen
    notify_transaction_changes = db.Column(db.Boolean, default=True)
    notify_wirtschaftsplan_changes = db.Column(db.Boolean, default=True)
    notify_user_changes = db.Column(db.Boolean, default=True)
    
    # Token für Passwort-Reset und E-Mail-Verifizierung
    def get_reset_token(self, expires_sec=1800):
        """Generiert ein Token für Passwort-Reset"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.id, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Überprüft ein Passwort-Reset-Token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = serializer.loads(
                token, 
                salt='password-reset-salt',
                max_age=expires_sec
            )
        except:
            return None
        return User.query.get(user_id)

# Klasse für Miteigentümer
# In models.py - Miteigentuemer-Klasse ergänzen
class Miteigentuemer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    mea = db.Column(db.Integer, nullable=False)  # Miteigentumsanteile
    vf_einheiten = db.Column(db.Integer, default=0)  # Verteilerfaktor-Einheiten
    tg_einheiten = db.Column(db.Integer, default=0)  # Tiefgaragen-Einheiten
    einheiten = db.Column(db.Integer, default=1)
    
    # Neues Feld für das Guthaben aus dem Vorjahr
    guthaben_vorjahr = db.Column(db.Numeric(10, 2), default=0.00)
    guthaben_jahr = db.Column(db.Integer, default=2023)  # Jahr, aus dem das Guthaben stammt
    
    def __repr__(self):
        return f'<Miteigentuemer {self.name}>'

# Klasse für Transaktion
class Transaktion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.Date, nullable=False)
    beschreibung = db.Column(db.Text, nullable=False)
    kategorie = db.Column(db.String(100))
    kostenart = db.Column(db.String(100))
    betrag = db.Column(db.Numeric(10, 2), nullable=False)
    umlagefaehig = db.Column(db.Boolean, default=False)
    
    # Verteilungsschlüssel (Einheiten, VF-Einheiten, TG-Einheiten)
    verteilungsschluessel = db.Column(db.String(20), default="Einheiten")
    
    # Optional: Direkte Miteigentümer-Zuordnung für Einzahlungen
    miteigentuemer_id = db.Column(db.Integer, db.ForeignKey('miteigentuemer.id'), nullable=True)
    miteigentuemer = db.relationship('Miteigentuemer', backref='transaktionen')
    
    jahr = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<Transaktion {self.beschreibung} {self.betrag}>'

# Klasse für Transaktionen mit Anhang
class TransaktionAnhang(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaktion_id = db.Column(db.Integer, db.ForeignKey('transaktion.id', ondelete='CASCADE'), nullable=False)
    dateiname = db.Column(db.String(255), nullable=False)
    original_dateiname = db.Column(db.String(255), nullable=False)
    dateityp = db.Column(db.String(50), nullable=False)  # z.B. 'pdf', 'jpg'
    hochgeladen_am = db.Column(db.DateTime, default=datetime.datetime.now)
    
    # Beziehung zur Transaktion
    transaktion = db.relationship('Transaktion', backref=db.backref('anhang', uselist=False, cascade='all, delete-orphan')) # uselist=False is nur 1 Anhang zur Transaktion
        
    def __repr__(self):
        return f'<TransaktionAnhang {self.dateiname}>'
        
    def get_file_path(self):
        """Gibt den vollständigen Dateipfad zurück"""
        from flask import current_app
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'rechnungen')
        return os.path.join(upload_folder, self.dateiname)
    
# Klasse zum Mapping zwischen Transaktion zu Wirtschaftsplankategorien bzw. Kostenarten
class KategorieKostenartMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wp_kategorie = db.Column(db.String(100), nullable=False)  # Wirtschaftsplan-Kategorie
    tx_kostenart = db.Column(db.String(100), nullable=False)  # Transaktions-Kostenart
    
    def __repr__(self):
        return f'<KategorieKostenartMapping {self.wp_kategorie} -> {self.tx_kostenart}>'

# Klasse für den Wirtschaftsplan   
class Wirtschaftsplan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jahr = db.Column(db.Integer, nullable=False)
    bezeichnung = db.Column(db.String(200), nullable=False)
    kategorie = db.Column(db.String(100), nullable=True)  # Für Gruppierung (z.B. "Betriebskosten", "Instandhaltung")
    betrag = db.Column(db.Numeric(10, 2), nullable=False)
    verteilungsschluessel = db.Column(db.String(50), nullable=False)  # Einheiten, VF-Einheiten, TG-Einheiten
    umlagefaehig = db.Column(db.Boolean, default=False)
    notiz = db.Column(db.Text, nullable=True)  # Optionale Notizen/Erläuterungen
    
    def __repr__(self):
        return f'<Wirtschaftsplan {self.jahr} {self.bezeichnung} {self.betrag}>'
# Klasse für Wirtschaftsplan mit MetaDaten
class WirtschaftsplanMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jahr = db.Column(db.Integer, nullable=False, unique=True)
    importiert_am = db.Column(db.DateTime, default=datetime.datetime.now)
    importiert_von = db.Column(db.Integer, db.ForeignKey('user.id'))
    dateiname = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='aktiv')  # 'aktiv', 'archiviert', 'entwurf'
    
    # Beziehung zum Benutzer, der den Import durchgeführt hat
    user = db.relationship('User', backref='wirtschaftsplaene')
    
    def __repr__(self):
        return f'<WirtschaftsplanMetadata {self.jahr}>'

# Klasse für den Kontostand
class Kontostand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.Date, nullable=False)
    betrag = db.Column(db.Numeric(10, 2), nullable=False)
    kommentar = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    user = db.relationship('User', backref='kontostände')
    
    def __repr__(self):
        return f'<Kontostand {self.datum} {self.betrag}>'

class RoadmapItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='planned')  # 'planned', 'in_progress', 'completed'
    timeframe = db.Column(db.String(20), nullable=False)  # 'short_term', 'medium_term', 'long_term'
    position = db.Column(db.Integer, default=0)  # Für die Sortierung
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<RoadmapItem {self.title}>'

class JahresabschlussKontostand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jahr = db.Column(db.Integer, nullable=False, unique=True)
    kontostand = db.Column(db.Numeric(10, 2), nullable=False)
    vorjahres_saldo = db.Column(db.Numeric(10, 2), nullable=False)
    kommentar = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    user = db.relationship('User', backref='jahresabschluesse')
    
    def __repr__(self):
        return f'<JahresabschlussKontostand {self.jahr} {self.kontostand}>'

class EmailConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def __repr__(self):
        return f'<EmailConfiguration {self.key}={self.value}>'
    
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # 'transaction', 'wirtschaftsplan', 'user', 'error'
    level = db.Column(db.String(20), nullable=False, index=True)  # 'info', 'warning', 'error'
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Beziehung zum Benutzer
    user = db.relationship('User', backref='log_entries')
    
    def __repr__(self):
        return f'<LogEntry {self.timestamp} {self.category} {self.level} {self.message[:50]}...>'

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    def __repr__(self):
        return f'<SystemSettings {self.key}={self.value}>'

# neue Klassen für Vorlagen

class BriefVorlage(db.Model):
    """Modell für Brief-Vorlagen wie Eigentümerversammlung, Umlaufbeschluss, Rundschreiben"""
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(200), nullable=False)
    typ = db.Column(db.String(50), nullable=False)  # 'eigentuemerversammlung', 'umlaufbeschluss', 'rundschreiben'
    inhalt = db.Column(db.Text, nullable=False)  # Der Vorlagentext mit Platzhaltern
    
    erstellt_von = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.datetime.now)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Beziehung zum Benutzer
    user = db.relationship('User', backref='brief_vorlagen')
    
    def __repr__(self):
        return f'<BriefVorlage {self.titel}>'


class TagesordnungspunktVorlage(db.Model):
    """Modell für Tagesordnungspunkte von Versammlungen"""
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=0)  # Reihenfolge in der Liste der TOPs
    status = db.Column(db.String(20), default='aktiv')  # 'aktiv', 'archiviert', 'entwurf'
    jahr = db.Column(db.Integer, nullable=True)

    erstellt_von = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    erstellt_am = db.Column(db.DateTime, default=datetime.datetime.now)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Beziehung zum Benutzer
    user = db.relationship('User', backref='tagesordnungspunkt_vorlagen')
    
    def __repr__(self):
        return f'<TagesordnungspunktVorlage {self.titel}>'


class WichtigesDokument(db.Model):
    """Modell für wichtige Dokumente wie Steuernummer, Hausordnung, DSGVO, Verträge"""
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text, nullable=True)
    kategorie = db.Column(db.String(50), nullable=False)  # 'steuernummer', 'hausordnung', 'dsgvo', 'vertraege'
    jahr = db.Column(db.Integer, nullable=True)  # Neues Feld für Jahr

    dateiname = db.Column(db.String(255), nullable=False)
    original_dateiname = db.Column(db.String(255), nullable=False)
    dateityp = db.Column(db.String(50), nullable=False)  # z.B. 'pdf', 'jpg'
    
    hochgeladen_von = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hochgeladen_am = db.Column(db.DateTime, default=datetime.datetime.now)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Beziehung zum Benutzer
    user = db.relationship('User', backref='wichtige_dokumente')
    
    def __repr__(self):
        return f'<WichtigesDokument {self.titel}>'
    
    def get_file_path(self):
        """Gibt den vollständigen Dateipfad zurück"""
        from flask import current_app
        import os
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dokumente')
        return os.path.join(upload_folder, self.dateiname)

class Selbstverwaltung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Mandatory fields
    name = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(200), nullable=False)
    plz = db.Column(db.String(10), nullable=False)
    ort = db.Column(db.String(100), nullable=False)
    land = db.Column(db.String(100), nullable=False, default='Deutschland')
    verwalter = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(50), nullable=False)
    
    # Optional fields
    beisitzer = db.Column(db.String(100), nullable=True)
    beisitzer_kontakt = db.Column(db.String(200), nullable=True)
    beirat_vorsitz = db.Column(db.String(100), nullable=True)
    beirat_vorsitz_kontakt = db.Column(db.String(200), nullable=True)
    beirat_mitglieder = db.Column(db.Text, nullable=True)  # Für mehrere Mitglieder
    beirat_mitglieder_kontakt = db.Column(db.Text, nullable=True)
    steuernummer = db.Column(db.String(50), nullable=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def __repr__(self):
        return f'<Selbstverwaltung {self.name}, {self.adresse}, {self.plz} {self.ort}>'
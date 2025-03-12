"""
Dashboard-Blueprint für die Startseite und allgemeine Übersicht
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from flask_login import login_required, current_user
import datetime

from models import db, Transaktion, Wirtschaftsplan, Miteigentuemer
from services.transaktion_service import get_transaction_statistics
from services.wirtschaftsplan_service import get_wirtschaftsplan_data
from services.kontostand_service import get_current_kontostand

dashboard_bp = Blueprint('dashboard', __name__)

def check_secret_key():
    """Prüft, ob SECRET_KEY konfiguriert ist"""
    secret_key = current_app.config.get('SECRET_KEY')
    return secret_key is not None and secret_key not in ['development', 'default_key', '', None]

@dashboard_bp.route('/')
def root():
    # Prüfen, ob SECRET_KEY konfiguriert ist
    if not check_secret_key():
        return redirect(url_for('setup.index'))
        
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Prüfen, ob SECRET_KEY konfiguriert ist
    if not check_secret_key():
        return redirect(url_for('setup.index'))
        
    # Verfügbare Jahre für Transaktionen
    tx_jahre = db.session.query(Transaktion.jahr).distinct().order_by(Transaktion.jahr.desc()).all()
    tx_jahre = [j[0] for j in tx_jahre]
    
    # Wirtschaftsplan-Jahre
    wp_jahre = db.session.query(Wirtschaftsplan.jahr).distinct().order_by(Wirtschaftsplan.jahr.desc()).all()
    wp_jahre = [j[0] for j in wp_jahre]
    
    # Kombiniere alle verfügbaren Jahre
    alle_jahre = list(set(tx_jahre + wp_jahre))
    alle_jahre.sort(reverse=True)
    
    # Falls keine Jahre vorhanden sind, aktuelles Jahr hinzufügen
    if not alle_jahre:
        alle_jahre.append(datetime.date.today().year)
    
    # Jahr aus Session oder Request-Args
    if 'reset_filters' in request.args:
        session.pop('dashboard_jahr', None)
    
    # Filter aus Request oder Session laden
    jahr = request.args.get('jahr', session.get('dashboard_jahr', datetime.date.today().year), type=int)
    
    # Aktuelles Jahr in der Session speichern
    session['dashboard_jahr'] = jahr
    
    # Statistiken für das ausgewählte Jahr abrufen
    transaktionen_stats = get_transaction_statistics(jahr)
    
    # Wirtschaftsplandaten für das Jahr abrufen
    wirtschaftsplan_data = get_wirtschaftsplan_data(jahr)
    
    # Letzte Transaktionen (nur vom ausgewählten Jahr)
    letzte_transaktionen = Transaktion.query.filter_by(jahr=jahr).order_by(Transaktion.datum.desc()).limit(5).all()
    
    # Kostenverteilung nach Kostenarten für das ausgewählte Jahr
    kosten_nach_art = db.session.query(
        Transaktion.kostenart,
        db.func.sum(Transaktion.betrag)
    ).filter(
        Transaktion.jahr == jahr,
        Transaktion.betrag < 0  # Nur Ausgaben
    ).group_by(Transaktion.kostenart).all()
    
    # Einzahlungen nach Miteigentümern
    einzahlungen_nach_miteigentümer = db.session.query(
        Miteigentuemer.name,
        db.func.sum(Transaktion.betrag)
    ).join(
        Transaktion, Transaktion.miteigentuemer_id == Miteigentuemer.id
    ).filter(
        Transaktion.jahr == jahr,
        Transaktion.betrag > 0  # Nur Einzahlungen
    ).group_by(Miteigentuemer.name).all()

    # Aktuellen Kontostand abrufen
    kontostand=get_current_kontostand()
    
    # Dashboard-Daten rendern
    return render_template(
        'dashboard/dashboard.html',
        jahre=alle_jahre,
        jahr=jahr,
        transaktionen_stats=transaktionen_stats,
        wirtschaftsplan=wirtschaftsplan_data,
        letzte_transaktionen=letzte_transaktionen,
        kosten_nach_art=kosten_nach_art,
        kontostand=kontostand,
        einzahlungen_nach_miteigentuemer=einzahlungen_nach_miteigentümer
    )
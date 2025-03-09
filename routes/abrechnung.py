"""
Abrechnungs-Blueprint für die Erstellung und Anzeige von Abrechnungen
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import login_required
from decimal import Decimal
import datetime

from models import db, Miteigentuemer, Transaktion
from services.abrechnung_service import get_abrechnung_data, generate_abrechnung_detail
from utils import erstelle_abrechnung_pdf

abrechnung_bp = Blueprint('abrechnung', __name__, url_prefix='/abrechnung')

@abrechnung_bp.route('/', methods=['GET'])
@login_required
def uebersicht():
    jahre = db.session.query(Transaktion.jahr).distinct().order_by(Transaktion.jahr.desc()).all()
    jahre = [j[0] for j in jahre]
    
    # Jahr aus Session oder Request-Args
    if 'reset_filters' in request.args:
        session.pop('abrechnung_jahr', None)
    
    # Filter aus Request oder Session laden
    jahr = request.args.get('jahr', session.get('abrechnung_jahr', datetime.date.today().year), type=int)
    
    # Aktuelles Jahr in der Session speichern
    session['abrechnung_jahr'] = jahr
    
    # Abrechnungsdaten abrufen
    abrechnung_data = get_abrechnung_data(jahr)
    
    return render_template(
        'abrechnung/uebersicht.html',
        jahre=jahre,
        jahr=jahr,
        gesamt_einnahmen=abrechnung_data['gesamt_einnahmen'],
        gesamt_ausgaben=abrechnung_data['gesamt_ausgaben'],
        gesamt_umlagefaehig=abrechnung_data['gesamt_umlagefaehig'],
        gesamt_nicht_umlagefaehig=abrechnung_data['gesamt_nicht_umlagefaehig'],
        kostenarten_stats=abrechnung_data['kostenarten_stats'],
        abrechnungen=abrechnung_data['abrechnungen'],
        kosten_einheiten=abrechnung_data['kosten_einheiten'],
        kosten_vf=abrechnung_data['kosten_vf'],
        kosten_tg=abrechnung_data['kosten_tg']
    )

@abrechnung_bp.route('/detail/<int:miteigentuemer_id>/<int:jahr>', methods=['GET'])
@login_required
def detail(miteigentuemer_id, jahr):
    # Abrechnungsdetails abrufen
    detail_data = generate_abrechnung_detail(miteigentuemer_id, jahr)
    
    if not detail_data:
        flash('Miteigentümer oder Daten nicht gefunden')
        return redirect(url_for('abrechnung.uebersicht'))
    
    return render_template(
        'abrechnung/detail.html',
        miteigentuemer=detail_data['miteigentuemer'],
        jahr=jahr,
        einzahlungen=detail_data['einzahlungen'],
        summe_einzahlungen=detail_data['summe_einzahlungen'],
        anteil_einheiten=detail_data['anteil_einheiten'],
        anteil_vf=detail_data['anteil_vf'],
        anteil_tg=detail_data['anteil_tg'],
        anteil_gesamt=detail_data['anteil_gesamt'],
        anteil_umlagefaehig=detail_data['anteil_umlagefaehig'],
        anteil_nicht_umlagefaehig=detail_data['anteil_nicht_umlagefaehig'],
        saldo=detail_data['saldo'],
        kosten_details=detail_data['kosten_details'],
        anteil_mea=detail_data['anteil_mea']
    )

@abrechnung_bp.route('/export/<int:miteigentuemer_id>/<int:jahr>', methods=['GET'])
@login_required
def export(miteigentuemer_id, jahr):
    """Exportiert die Abrechnung als PDF"""
    # Abrechnungsdetails abrufen
    detail_data = generate_abrechnung_detail(miteigentuemer_id, jahr)
    
    if not detail_data:
        flash('Miteigentümer oder Daten nicht gefunden')
        return redirect(url_for('abrechnung.uebersicht'))
    
    # PDF erstellen
    pdf_buffer = erstelle_abrechnung_pdf(
        detail_data['miteigentuemer'], 
        jahr, 
        detail_data['einzahlungen'], 
        detail_data['kosten_details'],
        detail_data['anteil_mea'],
        detail_data['anteil_umlagefaehig'], 
        detail_data['anteil_nicht_umlagefaehig'], 
        detail_data['anteil_gesamt'], 
        detail_data['saldo']
    )
    
    # PDF als Download anbieten
    dateiname = f"abrechnung_{detail_data['miteigentuemer'].name.replace(' ', '_')}_{jahr}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=dateiname,
        mimetype='application/pdf'
    )
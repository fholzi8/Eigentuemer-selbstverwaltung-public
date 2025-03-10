"""
Miteigentümer-Blueprint zur Verwaltung von Miteigentümern
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Miteigentuemer
from datetime import datetime
from decimal import Decimal

miteigentuemer_bp = Blueprint('miteigentuemer', __name__, url_prefix='/miteigentuemer')

@miteigentuemer_bp.route('/', methods=['GET'])
@login_required
def liste():
    # Alle Miteigentümer abfragen
    miteigentuemer = Miteigentuemer.query.all()
    
    # Berechnung der Gesamt-MEA für die Prozentanzeige
    gesamt_mea = sum(m.mea for m in miteigentuemer) if miteigentuemer else 1
    
    # Vorjahr für die Anzeige bestimmen (aktuelles Jahr - 1)
    vorjahr = datetime.now().year - 1
    
    return render_template('miteigentuemer/liste.html', 
                          miteigentuemer=miteigentuemer,
                          vorjahr=vorjahr,
                          gesamt_mea=gesamt_mea)

@miteigentuemer_bp.route('/neu', methods=['GET', 'POST'])
@login_required
def neu():
    # Vorjahr für die Anzeige bestimmen (aktuelles Jahr - 1)
    vorjahr = datetime.now().year - 1
    
    if request.method == 'POST':
        name = request.form.get('name')
        mea = request.form.get('mea', 0, type=int)
        vf_einheiten = request.form.get('vf_einheiten', 0, type=int)
        tg_einheiten = request.form.get('tg_einheiten', 0, type=int)
        einheiten = request.form.get('einheiten', 1, type=int)
        
        # Guthaben aus Vorjahr - Standardwert 0.00 setzen
        guthaben_vorjahr = request.form.get('guthaben_vorjahr', type=float, default=0.00)
        guthaben_jahr = request.form.get('guthaben_jahr', type=int, default=vorjahr)
        
        miteigentuemer = Miteigentuemer(
            name=name,
            mea=mea,
            vf_einheiten=vf_einheiten,
            tg_einheiten=tg_einheiten,
            einheiten=einheiten,
            guthaben_vorjahr=Decimal(str(guthaben_vorjahr)),
            guthaben_jahr=guthaben_jahr
        )
        
        try:
            db.session.add(miteigentuemer)
            db.session.commit()
            flash('Miteigentümer erfolgreich hinzugefügt')
            return redirect(url_for('miteigentuemer.liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen des Miteigentümers: {str(e)}')
   
    # Jahre für die Auswahl im Formular (Vorjahr bis Vorjahr-3)
    jahre = list(range(vorjahr-3, vorjahr+1))
    
    return render_template('miteigentuemer/neu.html', vorjahr=vorjahr, jahre=jahre)

@miteigentuemer_bp.route('/<int:miteigentuemer_id>', methods=['GET', 'POST'])
@login_required
def bearbeiten(miteigentuemer_id):
    miteigentuemer = Miteigentuemer.query.get_or_404(miteigentuemer_id)
    
    if request.method == 'POST':
        # Bestehende Felder aktualisieren
        miteigentuemer.name = request.form.get('name')
        miteigentuemer.mea = request.form.get('mea', type=int)
        miteigentuemer.vf_einheiten = request.form.get('vf_einheiten', type=int, default=0)
        miteigentuemer.tg_einheiten = request.form.get('tg_einheiten', type=int, default=0)
        miteigentuemer.einheiten = request.form.get('einheiten', type=int, default=1)
        
        # Neues Feld: Guthaben aus Vorjahr
        guthaben_vorjahr = request.form.get('guthaben_vorjahr', type=float, default=0.00)
        miteigentuemer.guthaben_vorjahr = Decimal(str(guthaben_vorjahr))
        miteigentuemer.guthaben_jahr = request.form.get('guthaben_jahr', type=int, default=2023)
        
        db.session.commit()
        flash(f'Miteigentümer {miteigentuemer.name} wurde aktualisiert', 'success')
        return redirect(url_for('miteigentuemer.liste'))
    
    # Vorjahr für die Anzeige bestimmen (aktuelles Jahr - 1)
    vorjahr = datetime.datetime.now().year - 1
    
    return render_template('miteigentuemer/bearbeiten.html', 
                          miteigentuemer=miteigentuemer,
                          vorjahr=vorjahr)
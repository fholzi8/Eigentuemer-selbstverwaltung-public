"""
Miteigentümer-Blueprint zur Verwaltung von Miteigentümern
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Miteigentuemer

miteigentuemer_bp = Blueprint('miteigentuemer', __name__, url_prefix='/miteigentuemer')

@miteigentuemer_bp.route('/', methods=['GET'])
@login_required
def liste():
    miteigentuemer = Miteigentuemer.query.all()
    gesamt_mea = sum(m.mea for m in miteigentuemer) if miteigentuemer else 1
    return render_template('miteigentuemer/liste.html', miteigentuemer=miteigentuemer, gesamt_mea=gesamt_mea)

@miteigentuemer_bp.route('/neu', methods=['GET', 'POST'])
@login_required
def neu():
    if request.method == 'POST':
        name = request.form.get('name')
        mea = request.form.get('mea', 0, type=int)
        vf_einheiten = request.form.get('vf_einheiten', 0, type=int)
        tg_einheiten = request.form.get('tg_einheiten', 0, type=int)
        einheiten = request.form.get('einheiten', 1, type=int)
        
        miteigentuemer = Miteigentuemer(
            name=name,
            mea=mea,
            vf_einheiten=vf_einheiten,
            tg_einheiten=tg_einheiten,
            einheiten=einheiten
        )
        
        try:
            db.session.add(miteigentuemer)
            db.session.commit()
            flash('Miteigentümer erfolgreich hinzugefügt')
            return redirect(url_for('miteigentuemer.liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen des Miteigentümers: {str(e)}')
    
    return render_template('miteigentuemer/neu.html')

@miteigentuemer_bp.route('/<int:miteigentuemer_id>', methods=['GET', 'POST'])
@login_required
def bearbeiten(miteigentuemer_id):
    miteigentuemer = Miteigentuemer.query.get_or_404(miteigentuemer_id)
    
    if request.method == 'POST':
        miteigentuemer.name = request.form.get('name')
        miteigentuemer.mea = request.form.get('mea', 0, type=int)
        miteigentuemer.vf_einheiten = request.form.get('vf_einheiten', 0, type=int)
        miteigentuemer.tg_einheiten = request.form.get('tg_einheiten', 0, type=int)
        miteigentuemer.einheiten = request.form.get('einheiten', 1, type=int)
        
        try:
            db.session.commit()
            flash('Miteigentümer aktualisiert')
            return redirect(url_for('miteigentuemer.liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Aktualisieren: {str(e)}')
    
    return render_template('miteigentuemer/bearbeiten.html', miteigentuemer=miteigentuemer)
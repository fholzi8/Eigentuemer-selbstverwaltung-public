"""Anpassung der Selbstverwaltung - Name als mandatory Feld + Änderung bei Brief-vorlage

Revision ID: cebd3d623c59
Revises: 468c1c7db981
Create Date: 2025-03-17 23:35:31.828672

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cebd3d623c59'
down_revision = '468c1c7db981'
branch_labels = None
depends_on = None

def upgrade():
    # Für SQLite müssen wir eine alternative Strategie verwenden, um NOT NULL-Spalten hinzuzufügen
    # 1. Prüfen, ob die Tabelle überhaupt existiert
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Wenn die Tabelle noch nicht existiert, nichts tun (das Modell wird die Spalte bei Erstellung enthalten)
    if 'selbstverwaltung' not in tables:
        return
        
    # 2. Alle Spalten der vorhandenen Tabelle ermitteln
    columns = inspector.get_columns('selbstverwaltung')
    column_names = [col['name'] for col in columns]
    
    # 3. Temporäre Tabelle erstellen, die alle bisherigen Spalten plus die neue Spalte enthält
    op.create_table('_selbstverwaltung_temp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, server_default='WEG'),  # Neue Spalte mit Default-Wert
        sa.Column('adresse', sa.String(length=200), nullable=False),
        sa.Column('plz', sa.String(length=10), nullable=False),
        sa.Column('ort', sa.String(length=100), nullable=False),
        sa.Column('land', sa.String(length=100), nullable=False),
        sa.Column('verwalter', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('telefon', sa.String(length=50), nullable=False),
        sa.Column('beisitzer', sa.String(length=100), nullable=True),
        sa.Column('beisitzer_kontakt', sa.String(length=200), nullable=True),
        sa.Column('beirat_vorsitz', sa.String(length=100), nullable=True),
        sa.Column('beirat_vorsitz_kontakt', sa.String(length=200), nullable=True),
        sa.Column('beirat_mitglieder', sa.Text(), nullable=True),
        sa.Column('beirat_mitglieder_kontakt', sa.Text(), nullable=True),
        sa.Column('steuernummer', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. Daten aus der alten Tabelle in die temporäre Tabelle kopieren
    # Sichere alle vorhandenen Spalten
    column_list = ', '.join([col for col in column_names])
    op.execute(f"INSERT INTO _selbstverwaltung_temp(id, name, {column_list}) SELECT id, 'WEG', {column_list} FROM selbstverwaltung")
    
    # 5. Alte Tabelle löschen und neue umbenennen
    op.drop_table('selbstverwaltung')
    op.rename_table('_selbstverwaltung_temp', 'selbstverwaltung')

def downgrade():
    # Bei Bedarf können wir die name-Spalte entfernen
    with op.batch_alter_table('selbstverwaltung', schema=None) as batch_op:
        batch_op.drop_column('name')
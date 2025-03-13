"""
Skript zur Initialisierung der Datenbank und zum Einfügen von Beispieldaten
"""

import os
import sys
import datetime
from decimal import Decimal
from pathlib import Path

# Pfad zum Projektverzeichnis hinzufügen (falls nötig)
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Flask-Anwendung importieren
from app import app, db
from models import User, Miteigentuemer, Transaktion, Wirtschaftsplan, WirtschaftsplanMetadata

def create_admin():
    """Erstellt einen Admin-Benutzer"""
    admin = User(username='admin', is_admin=True)
    admin.set_password('admin123')  # Im Produktivbetrieb ändern!
    db.session.add(admin)
    print("Admin-Benutzer erstellt.")

def create_miteigentuemer():
    """Erstellt Beispiel-Miteigentümer"""
    miteigentuemer_data = [
        {"name": "Florian Holzapfel und Roswitha Böhm", "mea": 70327, "vf_einheiten": 0, "tg_einheiten": 1, "einheiten": 1},
        {"name": "DOMDEY Irmgard", "mea": 89862, "vf_einheiten": 0, "tg_einheiten": 1, "einheiten": 1},
        {"name": "Margerete Häusler-Canstein & Birgit Canstein", "mea": 67722, "vf_einheiten": 0, "tg_einheiten": 1, "einheiten": 1},
        {"name": "ErbG: Jutta Koneberg-Freisinger & Söhne", "mea": 70327, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "Marlen Ulrike & Werner Altenburg", "mea": 101282, "vf_einheiten": 0, "tg_einheiten": 0, "einheiten": 1},
        {"name": "KLEMISCH Rositha", "mea": 77837, "vf_einheiten": 0, "tg_einheiten": 1, "einheiten": 1},
        {"name": "Elfriede & Erich Steurer", "mea": 54098, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "JANSCH Christina", "mea": 54098, "vf_einheiten": 0, "tg_einheiten": 1, "einheiten": 1},
        {"name": "BEKIM Dani Und Besa", "mea": 54098, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "ErbG: Markus Friedrich Köpp & Ulrike Carolin Binsmaier", "mea": 54098, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "ErbG Bauer", "mea": 54098, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "SCHWEPFINGER Christopher", "mea": 54098, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "Erb Kabisch", "mea": 54098, "vf_einheiten": 1, "tg_einheiten": 1, "einheiten": 1},
        {"name": "Ali Shekar & Rezvan Dokht Nazari", "mea": 143957, "vf_einheiten": 0, "tg_einheiten": 1, "einheiten": 1}
    ]
    
    for m_data in miteigentuemer_data:
        miteigentuemer = Miteigentuemer(**m_data)
        db.session.add(miteigentuemer)
    
    print(f"{len(miteigentuemer_data)} Miteigentümer erstellt.")

def create_example_transaktionen():
    """Erstellt Beispiel-Transaktionen"""
    # Aktuelles Jahr
    current_year = datetime.date.today().year
    
    # Beispiel-Transaktionen
    transaktionen_data = [
        # Einzahlungen (positiv)
        {
            "datum": datetime.date(current_year, 2, 25),
            "beschreibung": "Überweisung - Werner Altenburg - Werner Altenburg, Einzahlung Haus 5",
            "kategorie": "Matera SAS",
            "kostenart": "Einzahlung",
            "betrag": Decimal("300.00"),
            "umlagefaehig": False,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": 5,  # Marlen Ulrike & Werner Altenburg
            "jahr": current_year
        },
        {
            "datum": datetime.date(current_year, 1, 2),
            "beschreibung": "Überweisung - Christopher Schwepfinger - Haushaltsplan fuer Friedrichshafener Strasse 59",
            "kategorie": "WEG Friedrichshafener Str. 37 - 63",
            "kostenart": "Einzahlung",
            "betrag": Decimal("700.00"),
            "umlagefaehig": False,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": 12,  # SCHWEPFINGER Christopher
            "jahr": current_year
        },
        {
            "datum": datetime.date(current_year - 1, 6, 26),
            "beschreibung": "Überweisung - Irmgard Domdey - Hausgeld 2024",
            "kategorie": "WEG Friedrichshafener str. 37-63",
            "kostenart": "Einzahlung",
            "betrag": Decimal("500.00"),
            "umlagefaehig": False,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": 2,  # DOMDEY Irmgard
            "jahr": current_year - 1
        },
        
        # Ausgaben (negativ) - Verteilungsschlüssel: Einheiten
        {
            "datum": datetime.date(current_year, 1, 28),
            "beschreibung": "Bankeinzug - Friedrichshafener Str. 37, Abschlag Strom 01/2025 Betrag 33,00 Eur",
            "kategorie": "Strom",
            "kostenart": "Strom",
            "betrag": Decimal("-33.00"),
            "umlagefaehig": True,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year
        },
        {
            "datum": datetime.date(current_year, 1, 27),
            "beschreibung": "Überweisung - Rechnung Nr 20250221",
            "kategorie": "Sonstige",
            "kostenart": "Sonstige",
            "betrag": Decimal("-471.84"),
            "umlagefaehig": True,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year
        },
        {
            "datum": datetime.date(current_year - 1, 10, 15),
            "beschreibung": "Bankeinzug - REF-9C8269B20782A844AE",
            "kategorie": "Matera",
            "kostenart": "Verwaltung",
            "betrag": Decimal("-2866.00"),
            "umlagefaehig": True,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        },
        {
            "datum": datetime.date(current_year - 1, 10, 4),
            "beschreibung": "Bankeinzug - 09/2024 K-NR. 906623520-1 V-NR. 950327453",
            "kategorie": "Vodafone Deutschland GmbH",
            "kostenart": "Telekommunikation",
            "betrag": Decimal("-854.66"),
            "umlagefaehig": True,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        },
        {
            "datum": datetime.date(current_year - 1, 6, 17),
            "beschreibung": "Bankeinzug - HAFT UNF HE-1051-3372 04.06.2024",
            "kategorie": "Versicherungskammer Bayern",
            "kostenart": "Versicherung",
            "betrag": Decimal("-70.66"),
            "umlagefaehig": True,
            "verteilungsschluessel": "Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        },
        
        # Ausgaben (negativ) - Verteilungsschlüssel: VF-Einheiten (nur Wohnungen)
        {
            "datum": datetime.date(current_year, 1, 27),
            "beschreibung": "Überweisung - Schilder fuer Feuerloescher in Wohnbereich",
            "kategorie": "Instandhaltung",
            "kostenart": "Instandhaltung",
            "betrag": Decimal("-5.99"),
            "umlagefaehig": True,
            "verteilungsschluessel": "VF-Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year
        },
        {
            "datum": datetime.date(current_year - 1, 7, 22),
            "beschreibung": "Überweisung - Thermoflam Gemeinschaftsfläche",
            "kategorie": "Auslagen & Rückerstattung",
            "kostenart": "Instandhaltung",
            "betrag": Decimal("-49.99"),
            "umlagefaehig": True,
            "verteilungsschluessel": "VF-Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        },
        {
            "datum": datetime.date(current_year - 1, 5, 22),
            "beschreibung": "Überweisung - Materialkosten für Gemeinschaftsfläche",
            "kategorie": "Instandhaltung",
            "kostenart": "Instandhaltung",
            "betrag": Decimal("-200.00"),
            "umlagefaehig": True,
            "verteilungsschluessel": "VF-Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        },
        
        # Ausgaben (negativ) - Verteilungsschlüssel: TG-Einheiten (nur TG-Plätze)
        {
            "datum": datetime.date(current_year, 1, 27),
            "beschreibung": "Überweisung - alte Feuerloescher für TG",
            "kategorie": "Instandhaltung",
            "kostenart": "Instandhaltung",
            "betrag": Decimal("-20.00"),
            "umlagefaehig": True,
            "verteilungsschluessel": "TG-Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year
        },
        {
            "datum": datetime.date(current_year - 1, 10, 8),
            "beschreibung": "Überweisung - Rechnung Nr. 2024_040 mit Kundennummer: 10247 - TG-Einfahrt",
            "kategorie": "Kleines Bauunternehmen Würmtal",
            "kostenart": "Instandhaltung",
            "betrag": Decimal("-4533.28"),
            "umlagefaehig": True,
            "verteilungsschluessel": "TG-Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        },
        {
            "datum": datetime.date(current_year - 1, 6, 14),
            "beschreibung": "Übertragung - Rücklagen für TG-Sanierung",
            "kategorie": "WEG Friedrichshafener Str. 41",
            "kostenart": "Rücklage",
            "betrag": Decimal("-5000.00"),
            "umlagefaehig": False,
            "verteilungsschluessel": "TG-Einheiten",
            "miteigentuemer_id": None,
            "jahr": current_year - 1
        }
    ]
    
    for t_data in transaktionen_data:
        transaktion = Transaktion(**t_data)
        db.session.add(transaktion)
    
    print(f"{len(transaktionen_data)} Transaktionen erstellt.")

def create_wirtschaftsplan():
    """Erstellt einen Beispiel-Wirtschaftsplan"""
    current_year = datetime.date.today().year
    
    wirtschaftsplan_data = [
        {
            "jahr": current_year,
            "bezeichnung": "Materialkosten für Gemeinschaftsfläche",
            "kategorie": "Instandhaltung",
            "betrag": Decimal("200.00"),
            "verteilungsschluessel": "VF-Einheiten",
            "umlagefaehig": True,
            "notiz": "Basierend auf Vorjahreswerten"
        },
        {
            "jahr": current_year,
            "bezeichnung": "Hausmeisterkosten - Einheiten",
            "kategorie": "Betriebskosten",
            "betrag": Decimal("1432.32"),
            "verteilungsschluessel": "Einheiten",
            "umlagefaehig": True,
            "notiz": "Vertrag mit Ibrahimovic"
        },
        {
            "jahr": current_year,
            "bezeichnung": "Haftpflichtversicherung",
            "kategorie": "Versicherungen",
            "betrag": Decimal("70.66"),
            "verteilungsschluessel": "Einheiten",
            "umlagefaehig": True,
            "notiz": "Versicherungskammer Bayern"
        },
        {
            "jahr": current_year,
            "bezeichnung": "Materialkosten für TG und Aufgang",
            "kategorie": "Instandhaltung",
            "betrag": Decimal("500.00"),
            "verteilungsschluessel": "TG-Einheiten",
            "umlagefaehig": True,
            "notiz": "Schätzung"
        },
        {
            "jahr": current_year,
            "bezeichnung": "Instandhaltungsrückstellung",
            "kategorie": "Rücklagen",
            "betrag": Decimal("8000.00"),
            "verteilungsschluessel": "Einheiten",
            "umlagefaehig": False,
            "notiz": "Vorsorge für größere Reparaturen"
        },
        {
            "jahr": current_year,
            "bezeichnung": "Matera Verwaltungs-/Supportkosten",
            "kategorie": "Verwaltung",
            "betrag": Decimal("2016.00"),
            "verteilungsschluessel": "Einheiten",
            "umlagefaehig": True,
            "notiz": "Neuer Tarif ab 2025"
        }
    ]
    
    for w_data in wirtschaftsplan_data:
        wirtschaftsplan = Wirtschaftsplan(**w_data)
        db.session.add(wirtschaftsplan)
    
    # Metadaten für den Wirtschaftsplan
    metadata = WirtschaftsplanMetadata(
        jahr=current_year,
        importiert_am=datetime.datetime.now(),
        dateiname="Manuell erstellt",
        status="aktiv"
    )
    db.session.add(metadata)
    
    print(f"{len(wirtschaftsplan_data)} Wirtschaftsplan-Einträge erstellt.")

def init_db():
    """Initialisiert die Datenbank und fügt Beispieldaten ein"""
    with app.app_context():
        # Stellen Sie sicher, dass der Upload-Ordner existiert
        os.makedirs(os.path.join(app.config['BASE_DIR'], 'uploads'), exist_ok=True)
        
        # Datenbank neu erstellen
        db.drop_all()
        db.create_all()
        
        # Beispieldaten einfügen
        create_admin()
        create_miteigentuemer()
        create_example_transaktionen()
        create_wirtschaftsplan()
        
        # Änderungen speichern
        db.session.commit()
        
        print("Datenbank wurde initialisiert und mit Beispieldaten gefüllt.")

if __name__ == '__main__':
    init_db()
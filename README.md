WEG-Abrechnungsanwendung ist eine Flask Anwendung
==================================================

Diese Flask-Web-Anwendung ist für die Verwaltung und Abrechnung einer Wohneigentümergemeinschaft (WEG) 
entwickelt worden mit die folgende Hauptfunktionen bietet: 

1. Transaktionsverwaltung: Import von Banktransaktionen aus CSV/Excel, manuelle Erfassung und Bearbeitung 
2. Miteigentümerverwaltung: Verwaltung der Miteigentümer mit ihren verschiedenen Anteilen (MEA, VF-Einheiten, TG-Einheiten) 
3. Abrechnungssystem: Erstellung von Abrechnungen mit korrekter Kostenverteilung nach Verteilungsschlüsseln 
4. Wirtschafsplanverwaltung: Erstellung eines Wirtschaftsplan mit korrekter Kostenverteilung nach Verteilungsschlüsseln 
5. Benutzerverwaltung von mehreren Benutzer (Rollen: Admin + Benutzer)
6. Datenexport von Transaktionen, Kontostand, Wirtschaftsplan und DB-Backup (letztes fehlt nocht)
7. PDF-Export: Erstellung detaillierter PDF-Abrechnungen pro Miteigentümer Besonderheiten der Implementierung 
    
    * Drei verschiedene Verteilungsschlüssel: 
        ** Einheiten: Alle Miteigentümer zahlen anteilig 
        ** VF-Einheiten: Nur Miteigentümer mit Wohnungen (VF=1) zahlen 
        ** TG-Einheiten: Nur Miteigentümer mit Tiefgaragenplätzen (TG=1) zahlen 
    * Unterscheidung zwischen umlagefähigen und nicht umlagefähigen Kosten 
    * Benutzeroberfläche mit Bootstrap und responsivem Design 
    * PDF-Export der Abrechnungen mit ReportLab 

Behobene Technische Probleme 
    1. Python-Versionskompatibilität (besonders für pandas) 
    2. Typfehler bei Decimal/Float-Berechnungen 
    3. Rendering-Probleme im Chrome-Browser 
    4. Division-by-Zero-Fehler in der Benutzeroberfläche 
    5. PDF-Formatierungsfehler 

Roadmap: 

1. Weiterentwicklung der Anwendung: 
    * Vergleich von Wirtschaftsplan und tatsächlichen Kosten (Kategorien sind unterschiedlich) *check*
    * Rechnungen (pdf/jpeg) an Transaktionen anhängen *check*
    * Email-Versand für Änderungen bei Transaktionen/Wirtschaftsplan/Benutzer *check*
    * Benutzerauthentifizierung verstärken *progressing*
    * Mehrere Abrechnungszeiträume verwalten 
    * Verbesserung des PDF-Exports 
    * Kontostand online synchronisieren

2. Produktivdeploy: 
    * Konfiguration für sicheren Produktiveinsatz *check*
    * Rate-Limiter *check*
    * Content Security Policy *check but unsafe-mode*
    * wsgi (waitress) verwenden *check*
    * Secret Keys verstärken (config.py) *check*
    * Backup-Strategien für die Datenbank 
    * Optimierungen für bessere Performance 

3. Spezifische Anpassungen: 
    * Zusätzliche Verteilungsschlüssel 
    * Benutzerdefinierte Berichte 

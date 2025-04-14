WEG-Abrechnungsanwendung ist eine Flask Anwendung
==================================================

! Attention: Ich habe versehentlich ein paar Lösch-Funktionen und Darstellung bei Miteigentümer gelöscht. Korrigiert ist es im private branch, wenn jemand das benötigt bitte bei mir melden. Danke!

Diese Flask-Web-Anwendung ist für die Verwaltung und Abrechnung einer Wohneigentümergemeinschaft (WEG) 
entwickelt worden mit die folgende Hauptfunktionen bietet: 

![image](https://github.com/user-attachments/assets/fd5ba2b0-758e-4116-b1f7-9fc6afbb9b20)

1. Transaktionsverwaltung: Import von Banktransaktionen aus CSV/Excel, manuelle Erfassung und Bearbeitung 

![image](https://github.com/user-attachments/assets/cdfaf846-d477-4bab-a5db-b334ff090887)

2. Miteigentümerverwaltung: Verwaltung der Miteigentümer mit ihren verschiedenen Anteilen (MEA, VF-Einheiten, TG-Einheiten) 

![image](https://github.com/user-attachments/assets/8adfe59c-1f02-4458-9e80-b50e4b83cf79)

3. Abrechnungssystem: Erstellung von Abrechnungen mit korrekter Kostenverteilung nach Verteilungsschlüsseln 

![image](https://github.com/user-attachments/assets/301eee56-5e38-446c-a7a1-6c34712501c0)

4. Wirtschafsplanverwaltung: Erstellung eines Wirtschaftsplan mit korrekter Kostenverteilung nach Verteilungsschlüsseln 

![image](https://github.com/user-attachments/assets/bbf915d1-938f-44ff-ad68-230abf9db4a4)

5. Benutzerverwaltung von mehreren Benutzer (Rollen: Admin + Benutzer)

6. Datenexport von Transaktionen, Kontostand, Wirtschaftsplan und DB-Backup (letztes fehlt nocht)

7. PDF-Export: Erstellung detaillierter PDF-Abrechnungen pro Miteigentümer Besonderheiten der Implementierung 

    * Drei verschiedene Verteilungsschlüssel:
        * Einheiten: Alle Miteigentümer zahlen anteilig
        * VF-Einheiten: Nur Miteigentümer mit Wohnungen (VF=1) zahlen
        * TG-Einheiten: Nur Miteigentümer mit Tiefgaragenplätzen (TG=1) zahlen 
    * Unterscheidung zwischen umlagefähigen und nicht umlagefähigen Kosten 
    * Benutzeroberfläche mit Bootstrap und responsivem Design 
    * PDF-Export der Abrechnungen mit ReportLab 

Folgende Sicherheitsmaßnahmen implementiert:

    * CSRF-Schutz
    * Content Security Policy (CSP)
    * Erweiterte Session-Konfiguration
    * Rate Limiting
    * Sichere Upload-Verarbeitung
    * Waitress für Produktionsdeployment

Behobene Technische Probleme:

    * Python-Versionskompatibilität (besonders für pandas) 
    * Typfehler bei Decimal/Float-Berechnungen
    * Rendering-Probleme im Chrome-Browser 
    * Division-by-Zero-Fehler in der Benutzeroberfläche
    * PDF-Formatierungsfehler
    * Globale Email-Settings nicht verlinkt


Es werden beim Starten der APP noch folgende Umgebungsvariablen benötigt:
    * SECRET_KEY
    * MAIL_PASSWORD # hier sollten die Globalen Emailsettings diese Funktion bald übernehmen

Roadmap: 

1. Weiterentwicklung der Anwendung: 
    * Mehrere Abrechnungszeiträume verwalten 
    * Verbesserung des PDF-Exports
    * Kontostand mit Jahresabschluss kombinieren 
    * Kontostand online synchronisieren
    * Mobile Ansicht optimieren
    * Touch-freundliche Bedienelemente

2. Produktivdeploy: 
    * Backup-Strategien für die Datenbank 
    * Optimierungen für bessere Performance 

3. Spezifische Anpassungen: 
    * Zusätzliche Verteilungsschlüssel 
    * Benutzerdefinierte Berichte 

# Eigentümer-Selbstverwaltung

## Container-Build-Anleitung

Diese Anleitung erklärt, wie du das Projekt in einem Container laufen lässt.

### Voraussetzungen

- Podman (oder Docker)
- Git
- Ein GitHub-Konto mit Zugriff auf das Repository

### SSH-Schlüssel für GitHub einrichten

1. **SSH-Schlüsselpaar generieren** (überspringen, wenn bereits vorhanden):
   ```bash
   ssh-keygen -t ed25519 -C "deine-email@example.com"
   ```
   Folge den Anweisungen. Es wird empfohlen, eine Passphrase zu verwenden.

2. **Öffentlichen Schlüssel zu GitHub hinzufügen**:
   - Kopiere den Inhalt deines öffentlichen Schlüssels:
     ```bash
     cat ~/.ssh/id_ed25519.pub
     ```
   - Gehe zu [GitHub Settings > SSH and GPG keys](https://github.com/settings/keys)
   - Klicke auf "New SSH key"
   - Gib einen Titel ein (z.B. "Mein Entwicklungsrechner")
   - Füge den kopierten öffentlichen Schlüssel ein
   - Klicke auf "Add SSH key"

3. **Teste die SSH-Verbindung zu GitHub**:
   ```bash
   ssh -T git@github.com
   ```
   Wenn du eine Meldung wie "Hi username! You've successfully authenticated..." siehst, hat alles funktioniert.

### Container bauen und ausführen

1. **Containerfile herunterladen**:
   Lade den Containerfile aus diesem Repository herunter.

2. **Container bauen**:
   ```bash
   # SSH-Key für den Build-Prozess bereitstellen
   SSH_PRIVATE_KEY=$(cat ~/.ssh/id_ed25519)
   
   # Container bauen
   podman build \
     --build-arg SSH_PRIVATE_KEY="$SSH_PRIVATE_KEY" \
     -t eigentuemer-selbstverwaltung:latest \
     -f Containerfile .
   ```

3. **Container ausführen**:
   ```bash
   # Ordner für persistente Daten erstellen
   mkdir -p ./daten/data ./daten/exports ./daten/config
   
   # Container mit gemounteten Volumes starten
   podman run -p 8000:8000 \
     -v ./daten/data:/app/data \
     -v ./daten/exports:/app/exports \
     -v ./daten/config:/app/config \
     eigentuemer-selbstverwaltung:latest
   ```
   Die Anwendung sollte nun unter http://localhost:8000 erreichbar sein.
   
   Der SECRET_KEY wird automatisch beim ersten Start generiert und in der Datei `/app/config/.env` gespeichert.

### Eigene Daten verwenden

1. **Daten-Verzeichnis nutzen**:
   Alle Dateien im `./daten/data`-Verzeichnis sind für die Anwendung verfügbar.

2. **Eigene .env-Datei verwenden**:
   Du kannst eine eigene `.env`-Datei erstellen:
   ```bash
   # Einen SECRET_KEY generieren
   SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   
   # .env-Datei erstellen
   echo "SECRET_KEY=$SECRET_KEY" > ./daten/config/.env
   ```

3. **Container mit eigenem SECRET_KEY starten**:
   ```bash
   podman run -p 8000:8000 \
     -v ./daten/data:/app/data \
     -v ./daten/exports:/app/exports \
     -v ./daten/config:/app/config \
     -e SECRET_KEY="mein-eigener-secret-key" \
     eigentuemer-selbstverwaltung:latest
   ```

### Container zu Docker Hub hochladen

1. **Bei Docker Hub anmelden**:
   ```bash
   podman login docker.io
   ```

2. **Image taggen**:
   ```bash
   podman tag eigentuemer-selbstverwaltung:latest docker.io/deinbenutzername/eigentuemer-selbstverwaltung:latest
   ```

3. **Image hochladen**:
   ```bash
   podman push docker.io/deinbenutzername/eigentuemer-selbstverwaltung:latest
   ```

## Wichtige Hinweise

### Port-Weiterleitung

Bei `-p 8000:8000`:
- Der erste Port (8000) ist der **Host-Port**, auf dem du die Anwendung erreichst
- Der zweite Port (8000) ist der **Container-Port**, auf dem die Anwendung im Container läuft

Du kannst den Host-Port ändern, z.B. `-p 80:8000`, um die Anwendung auf Port 80 zu erreichen.

### Sicherheitshinweise

- Der SSH-Schlüssel wird nur während des Build-Prozesses verwendet und nicht im finalen Container-Image gespeichert.
- Sensible Daten werden in gemounteten Volumes gespeichert und nicht im Container-Image.
- Der SECRET_KEY wird automatisch generiert oder kann als Umgebungsvariable übergeben werden.
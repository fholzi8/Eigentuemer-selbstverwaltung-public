# Build-Stage
FROM python:3.11-slim AS builder

# Installiere Git und SSH Client
RUN apt-get update && apt-get install -y git openssh-client && \
    rm -rf /var/lib/apt/lists/*

# Bereite SSH-Umgebung vor
RUN mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# Kopiere den SSH-Key vom Host in den Container (nur während des Builds verfügbar)
# Hinweis: Der SSH-Key wird nicht im finalen Image gespeichert
ARG SSH_PRIVATE_KEY
RUN echo "${SSH_PRIVATE_KEY}" > /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa

# Klone das Repository (öffentliche Version ohne sensible Daten)
RUN git clone git@github.com:fholzi8/Eigentuemer-selbstverwaltung-public.git /app

# Wechsle in das Verzeichnis
WORKDIR /app

# Installiere python-dotenv für Umgebungsvariablen-Management
RUN pip install --no-cache-dir -r requirements.txt python-dotenv

# Erstelle Verzeichnisse für Benutzerdaten
RUN mkdir -p /app/data /app/exports && \
    touch /app/data/.gitkeep /app/exports/.gitkeep

# Finales Image
FROM python:3.11-slim

# Installiere python-dotenv
RUN pip install --no-cache-dir python-dotenv

# Kopiere die Anwendung und installierte Pakete vom Builder-Image
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Setze Arbeitsverzeichnis
WORKDIR /app

# Erstelle einen Ordner für die .env-Datei und andere Konfigurationsdateien
RUN mkdir -p /app/config

# Erstelle Volumes für persistente Daten und Exporte
VOLUME ["/app/data", "/app/exports", "/app/config"]

# Setze Standardwert für SECRET_KEY, kann überschrieben werden
ARG SECRET_KEY
ENV SECRET_KEY=${SECRET_KEY}

# Skript zum Initialisieren der Umgebung beim Container-Start
RUN echo '#!/bin/bash\n\
if [ ! -f /app/config/.env ]; then\n\
  if [ -z "$SECRET_KEY" ]; then\n\
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")\n\
  fi\n\
  echo "SECRET_KEY=$SECRET_KEY" > /app/config/.env\n\
  echo "Neue .env-Datei mit SECRET_KEY erstellt"\n\
else\n\
  echo ".env-Datei existiert bereits, wird verwendet"\n\
fi\n\
\n\
# Starte die Anwendung\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Exponiere Port
EXPOSE 8000

# Starte die Anwendung mit dem Init-Skript
CMD ["/app/entrypoint.sh"]
#!/bin/bash
# backup.sh
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/path/to/backups"
APP_DIR="/path/to/app"

#cronjob
#0 2 * * * /path/to/backup.sh >> /path/to/backup.log 2>&1

# Datenbank sichern
mkdir -p $BACKUP_DIR/db
cp $APP_DIR/instance/weg.db $BACKUP_DIR/db/weg_$TIMESTAMP.db

# Uploads sichern
mkdir -p $BACKUP_DIR/uploads
tar -czf $BACKUP_DIR/uploads/uploads_$TIMESTAMP.tar.gz $APP_DIR/uploads/

# Ältere Backups löschen (behalte die letzten 30)
cd $BACKUP_DIR/db
ls -tp | grep -v '/$' | tail -n +31 | xargs -I {} rm -- {}
cd $BACKUP_DIR/uploads
ls -tp | grep -v '/$' | tail -n +31 | xargs -I {} rm -- {}
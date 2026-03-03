#!/usr/bin/env bash
# Setup-Skript für den Webhook-Cron-Job.
#
# Verwendung:
#   ./scripts/setup_cron.sh              # Standard: täglich um 08:00
#   ./scripts/setup_cron.sh "*/5 * * * *"  # Alle 5 Minuten

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SENDER="$PROJECT_DIR/captainhook/sender.py"
LOG_FILE="$PROJECT_DIR/webhook.log"
PYTHON="${PYTHON:-python3}"
SCHEDULE="${1:-0 8 * * *}"

# Verify sender script exists
if [ ! -f "$SENDER" ]; then
    echo "Fehler: $SENDER nicht gefunden." >&2
    exit 1
fi

CRON_LINE="$SCHEDULE cd $PROJECT_DIR && $PYTHON -m captainhook.sender >> $LOG_FILE 2>&1"

# Add to crontab (avoiding duplicates)
( crontab -l 2>/dev/null | grep -v "captainhook.sender" ; echo "$CRON_LINE" ) | crontab -

echo "Cron-Job eingerichtet:"
echo "  Zeitplan : $SCHEDULE"
echo "  Befehl   : cd $PROJECT_DIR && $PYTHON -m captainhook.sender"
echo "  Log-Datei: $LOG_FILE"
echo ""
echo "Aktuelle Crontab:"
crontab -l

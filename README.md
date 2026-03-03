# CaptainHook – Webhook-Plattform

Eine selbstgebaute Webhook-Plattform mit Python. Enthält einen Empfangsserver (Flask **oder** FastAPI), einen Sender-Client mit Retry-Logik sowie HMAC-Signaturprüfung.

## Schnellstart

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration anlegen
cp .env.example .env
# → .env bearbeiten und WEBHOOK_SECRET setzen
```

## Webhook-Server starten

### Option A – Flask

```bash
python -m captainhook.flask_server
```

### Option B – FastAPI

```bash
python -m captainhook.fastapi_server
```

Der Server lauscht standardmäßig auf Port **5000** (konfigurierbar über `WEBHOOK_PORT` in `.env`).

Endpunkte:

| Methode | Pfad       | Beschreibung             |
|---------|-----------|--------------------------|
| POST    | `/webhook` | Webhook-Ereignisse empfangen |
| GET     | `/health`  | Health-Check             |

## Webhook senden

```bash
python -m captainhook.sender
```

Der Sender liest `WEBHOOK_TARGET_URL` und `WEBHOOK_SECRET` aus der `.env`-Datei. Er signiert Anfragen automatisch per HMAC-SHA256 und wiederholt fehlgeschlagene Sendungen bis zu 3 Mal mit exponentiellem Backoff.

### Programmatisch verwenden

```python
from captainhook.sender import send_webhook

send_webhook({"event": "deploy", "data": {"version": "1.2.0"}})
```

## Cron-Job einrichten

```bash
# Standard: täglich um 08:00
./scripts/setup_cron.sh

# Benutzerdefinierter Zeitplan (z. B. alle 5 Minuten)
./scripts/setup_cron.sh "*/5 * * * *"
```

Oder manuell per `crontab -e`:

```
0 8 * * * cd /pfad/zu/captainhook && python3 -m captainhook.sender >> webhook.log 2>&1
```

## Sicherheit

- **HMAC-SHA256-Signatur:** Wird automatisch erzeugt und geprüft, wenn `WEBHOOK_SECRET` gesetzt ist.
- **Umgebungsvariablen:** Sensible Daten gehören in `.env`, nicht in den Quellcode.
- Für öffentliche Tests: `ngrok http 5000`

## Projektstruktur

```
captainhook/
├── captainhook/
│   ├── __init__.py
│   ├── flask_server.py    # Flask-Webhook-Server
│   ├── fastapi_server.py  # FastAPI-Webhook-Server
│   ├── sender.py          # Webhook-Sender mit Retry
│   └── security.py        # HMAC-Signatur-Erzeugung & -Prüfung
├── scripts/
│   └── setup_cron.sh      # Cron-Job-Einrichtung
├── .env.example            # Beispielkonfiguration
├── requirements.txt
├── LICENSE
└── README.md
```

## Lizenz

MIT – siehe [LICENSE](LICENSE).

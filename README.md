# CaptainHook – Webhook-Plattform

Eine selbstgebaute Webhook-Plattform mit Python. Enthält einen Empfangsserver (Flask **oder** FastAPI), einen Sender-Client mit Retry-Logik sowie HMAC-Signaturprüfung.

## Schnellstart

```bash
# Abhängigkeiten installieren
uv sync

# Konfiguration anlegen
cp .env.example .env
# → .env bearbeiten und WEBHOOK_SECRET setzen
```

## Webhook-Server starten

### Option A – Flask

```bash
uv run captainhook-flask
```

### Option B – FastAPI

```bash
uv run captainhook-fastapi
```

Der Server lauscht standardmäßig auf Port **5050** (konfigurierbar über `WEBHOOK_PORT` in `.env`).

### HTMX-Dashboard (Flask)

Der Flask-Server enthält ein Web-Dashboard unter `http://localhost:5050/`:

- **Live-Event-Log** – zeigt empfangene Webhooks in Echtzeit (Polling alle 3 s)
- **Test-Sender** – Webhooks direkt aus dem Browser verschicken
- **Health-Badge** – Serverstatus auf einen Blick

Endpunkte:

| Methode | Pfad       | Beschreibung             |
|---------|-----------|--------------------------|
| GET     | `/`        | HTMX-Dashboard           |
| POST    | `/webhook` | Webhook-Ereignisse empfangen |
| GET     | `/health`  | Health-Check             |

## Webhook senden

```bash
uv run captainhook-send
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
0 8 * * * cd /pfad/zu/captainhook && uv run captainhook-send >> webhook.log 2>&1
```

## Sicherheit

- **HMAC-SHA256-Signatur:** Wird automatisch erzeugt und geprüft, wenn `WEBHOOK_SECRET` gesetzt ist.
- **Umgebungsvariablen:** Sensible Daten gehören in `.env`, nicht in den Quellcode.
- Für öffentliche Tests: `ngrok http 5050`

## Projektstruktur

```
captainhook/
├── captainhook/
│   ├── __init__.py
│   ├── flask_server.py    # Flask-Webhook-Server + HTMX-Dashboard
│   ├── fastapi_server.py  # FastAPI-Webhook-Server
│   ├── sender.py          # Webhook-Sender mit Retry
│   ├── security.py        # HMAC-Signatur-Erzeugung & -Prüfung
│   └── templates/         # Jinja2/HTMX-Templates
├── scripts/
│   └── setup_cron.sh      # Cron-Job-Einrichtung
├── .env.example            # Beispielkonfiguration
├── pyproject.toml
├── LICENSE
└── README.md
```

## Lizenz

MIT – siehe [LICENSE](LICENSE).

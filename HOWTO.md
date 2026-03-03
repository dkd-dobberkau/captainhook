# HOWTO – CaptainHook Schritt für Schritt

## Voraussetzungen

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python-Paketmanager)

```bash
# uv installieren (falls noch nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 1. Projekt einrichten

```bash
git clone https://github.com/dkd-dobberkau/captainhook.git
cd captainhook

# Abhängigkeiten installieren
uv sync

# Konfigurationsdatei anlegen
cp .env.example .env
```

Öffne die `.env`-Datei und passe die Werte an:

```dotenv
WEBHOOK_SECRET=mein-geheimer-schluessel
WEBHOOK_PORT=5050
WEBHOOK_TARGET_URL=http://localhost:5050/webhook
```

> **Tipp:** `WEBHOOK_SECRET` kann ein beliebiger String sein. Er wird zur
> HMAC-SHA256-Signierung verwendet. Wenn er leer bleibt, wird keine
> Signaturprüfung durchgeführt.

---

## 2. Server starten

### Flask (mit HTMX-Dashboard)

```bash
uv run captainhook-flask
```

Öffne im Browser: **http://localhost:5050/**

Du siehst das Dashboard mit:
- einem Formular zum Versenden von Test-Webhooks
- einer Live-Liste der empfangenen Events
- einem Health-Badge im Header

### FastAPI (nur API, kein Dashboard)

```bash
uv run captainhook-fastapi
```

Die API-Docs sind unter **http://localhost:5050/docs** erreichbar.

---

## 3. Webhook manuell senden

### Über das Dashboard

1. Server starten (`uv run captainhook-flask`)
2. http://localhost:5050/ aufrufen
3. Event-Name und Payload ausfüllen
4. „Senden" klicken
5. Das Event erscheint sofort in der Liste darunter

### Über die Kommandozeile

```bash
uv run captainhook-send
```

Das sendet einen Test-Event (`{"event": "test", "data": "Hallo Welt"}`) an die
in `.env` konfigurierte `WEBHOOK_TARGET_URL`.

### Über curl

```bash
curl -X POST http://localhost:5050/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "deploy", "version": "1.0.0"}'
```

Mit Signatur (wenn `WEBHOOK_SECRET` gesetzt ist):

```bash
SECRET="mein-geheimer-schluessel"
PAYLOAD='{"event": "deploy", "version": "1.0.0"}'
SIGNATURE="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)"

curl -X POST http://localhost:5050/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

---

## 4. Webhook programmatisch senden

```python
from captainhook.sender import send_webhook

# Einfacher Aufruf (nutzt .env-Konfiguration)
send_webhook({"event": "user_registered", "user_id": 42})

# Mit expliziter URL und Secret
send_webhook(
    {"event": "deploy", "version": "2.0.0"},
    url="https://mein-server.de/webhook",
    secret="anderes-secret",
)
```

Die Funktion wiederholt fehlgeschlagene Sendungen automatisch bis zu 3 Mal
(2 s, 4 s, 8 s Wartezeit).

---

## 5. Cron-Job einrichten

### Automatisch

```bash
# Täglich um 08:00
./scripts/setup_cron.sh

# Alle 5 Minuten
./scripts/setup_cron.sh "*/5 * * * *"

# Stündlich
./scripts/setup_cron.sh "0 * * * *"
```

### Manuell

```bash
crontab -e
```

Zeile hinzufügen:

```
0 8 * * * cd /pfad/zu/captainhook && uv run captainhook-send >> webhook.log 2>&1
```

### Cron-Zeitplan-Referenz

```
┌───────────── Minute (0-59)
│ ┌─────────── Stunde (0-23)
│ │ ┌───────── Tag im Monat (1-31)
│ │ │ ┌─────── Monat (1-12)
│ │ │ │ ┌───── Wochentag (0-6, 0 = Sonntag)
│ │ │ │ │
* * * * *
```

| Beispiel          | Bedeutung                    |
|-------------------|------------------------------|
| `0 8 * * *`       | Täglich um 08:00             |
| `*/5 * * * *`     | Alle 5 Minuten               |
| `0 */2 * * *`     | Alle 2 Stunden               |
| `0 9 * * 1-5`     | Mo–Fr um 09:00               |
| `0 0 1 * *`       | Am 1. jedes Monats um 00:00  |

---

## 6. Sicherheit konfigurieren

### HMAC-Signatur aktivieren

Setze `WEBHOOK_SECRET` in der `.env`:

```dotenv
WEBHOOK_SECRET=ein-langer-zufaelliger-string
```

Danach werden:
- **Ausgehende Webhooks** automatisch mit einem `X-Webhook-Signature`-Header signiert
- **Eingehende Webhooks** auf gültige Signatur geprüft (ungültige werden mit `403` abgelehnt)

### Signatur deaktivieren

Entferne `WEBHOOK_SECRET` aus der `.env` oder setze es auf leer:

```dotenv
WEBHOOK_SECRET=
```

---

## 7. Für das Internet freigeben (ngrok)

Zum Testen mit externen Services (GitHub, Stripe, etc.):

```bash
# ngrok installieren: https://ngrok.com/download
ngrok http 5050
```

Die angezeigte URL (z. B. `https://abc123.ngrok.io`) kann als Webhook-URL in
externen Services eingetragen werden.

---

## 8. Health-Check

```bash
curl http://localhost:5050/health
# → {"status": "ok"}
```

Nützlich für Monitoring-Tools oder Load Balancer.

---

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| `Connection refused` | Server läuft nicht – `uv run captainhook-flask` starten |
| `403 Ungültige Signatur` | `WEBHOOK_SECRET` stimmt zwischen Sender und Empfänger nicht überein |
| `400 Ungültiges JSON` | Request-Body ist kein gültiges JSON |
| Cron-Job läuft nicht | `crontab -l` prüfen, absolute Pfade verwenden, Logs in `webhook.log` prüfen |

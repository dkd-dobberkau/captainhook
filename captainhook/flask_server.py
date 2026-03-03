"""Flask-based webhook server with HTMX dashboard and HMAC signature verification."""

import json
import logging
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import requests as req
from dotenv import load_dotenv
from flask import Flask, Response, render_template, request

from captainhook.security import generate_signature, verify_signature

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# In-memory event store (newest first, max 200 entries)
events: deque[dict] = deque(maxlen=200)


# ── Webhook API ──────────────────────────────────────────────────────────────


@app.route("/webhook", methods=["POST"])
def webhook() -> tuple[Response, int]:
    """Receive and process incoming webhook events."""
    if WEBHOOK_SECRET:
        signature = request.headers.get("X-Webhook-Signature", "")
        if not verify_signature(request.get_data(), WEBHOOK_SECRET, signature):
            logger.warning("Invalid signature from %s", request.remote_addr)
            return Response(
                json.dumps({"error": "Ungültige Signatur"}),
                status=403,
                content_type="application/json",
            )

    data = request.get_json(silent=True)
    if data is None:
        return Response(
            json.dumps({"error": "Ungültiges JSON"}),
            status=400,
            content_type="application/json",
        )

    now = datetime.now(timezone.utc)
    events.appendleft({"data": data, "timestamp": now.strftime("%H:%M:%S")})

    logger.info(
        "Webhook empfangen: event=%s, timestamp=%s",
        data.get("event", "unbekannt"),
        now.isoformat(),
    )

    return Response(
        json.dumps({"status": "erfolgreich"}),
        status=200,
        content_type="application/json",
    )


@app.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    """Health-check endpoint."""
    return Response(
        json.dumps({"status": "ok"}),
        status=200,
        content_type="application/json",
    )


# ── HTMX Dashboard ──────────────────────────────────────────────────────────


@app.route("/")
def dashboard() -> str:
    """Serve the main dashboard page."""
    return render_template("dashboard.html")


@app.route("/ui/events", methods=["GET"])
def ui_events() -> str:
    """Return the event list partial (polled by htmx)."""
    return render_template("partials/event_list.html", events=list(events))


@app.route("/ui/events", methods=["DELETE"])
def ui_clear_events() -> str:
    """Clear all stored events."""
    events.clear()
    return render_template("partials/event_list.html", events=[])


@app.route("/ui/health-badge")
def ui_health_badge() -> str:
    """Return the health badge partial."""
    return render_template("partials/health_badge.html", ok=True, status="Online")


@app.route("/ui/send", methods=["POST"])
def ui_send() -> str:
    """Send a webhook from the dashboard form."""
    event = request.form.get("event", "test")
    target = (
        request.form.get("target", "").strip()
        or f"http://localhost:{os.getenv('WEBHOOK_PORT', '5000')}/webhook"
    )
    raw_payload = request.form.get("payload", "{}").strip()

    try:
        extra = json.loads(raw_payload) if raw_payload else {}
    except json.JSONDecodeError:
        return '<span style="color:#fca5a5;">Ungültiges JSON im Payload.</span>'

    data = {"event": event, **extra}
    payload = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}

    if WEBHOOK_SECRET:
        headers["X-Webhook-Signature"] = generate_signature(payload, WEBHOOK_SECRET)

    try:
        resp = req.post(target, data=payload, headers=headers, timeout=10)
        color = "#6ee7b7" if resp.ok else "#fca5a5"
        return f'<span style="color:{color};">Status {resp.status_code} – {resp.text}</span>'
    except req.RequestException as exc:
        return f'<span style="color:#fca5a5;">Fehler: {exc}</span>'


def main() -> None:
    port = int(os.getenv("WEBHOOK_PORT", "5000"))
    logger.info("Flask-Webhook-Server startet auf Port %d", port)
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

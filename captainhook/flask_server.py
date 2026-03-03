"""Flask-based webhook server with optional HMAC signature verification."""

import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, request

from captainhook.security import verify_signature

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@app.route("/webhook", methods=["POST"])
def webhook() -> tuple[Response, int]:
    """Receive and process incoming webhook events."""
    # Signature verification (if a secret is configured)
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

    logger.info(
        "Webhook empfangen: event=%s, timestamp=%s",
        data.get("event", "unbekannt"),
        datetime.now(timezone.utc).isoformat(),
    )

    # --- Add your processing logic here ---

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


def main() -> None:
    port = int(os.getenv("WEBHOOK_PORT", "5000"))
    logger.info("Flask-Webhook-Server startet auf Port %d", port)
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

"""Webhook sender (client) with HMAC signing and retry logic."""

import json
import logging
import os
import time

import requests
from dotenv import load_dotenv

from captainhook.security import generate_signature

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_TARGET_URL = os.getenv(
    "WEBHOOK_TARGET_URL", "http://localhost:5050/webhook"
)
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each retry


def send_webhook(
    data: dict,
    url: str | None = None,
    secret: str | None = None,
    retries: int = MAX_RETRIES,
) -> requests.Response | None:
    """Send a webhook POST request with optional HMAC signing and retries.

    Args:
        data: JSON-serialisable payload.
        url: Target URL (falls back to WEBHOOK_TARGET_URL env var).
        secret: HMAC secret (falls back to WEBHOOK_SECRET env var).
        retries: Number of retry attempts on failure.

    Returns:
        The Response object on success, or None after all retries failed.
    """
    target = url or WEBHOOK_TARGET_URL
    signing_secret = secret or WEBHOOK_SECRET

    payload = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}

    if signing_secret:
        headers["X-Webhook-Signature"] = generate_signature(
            payload, signing_secret
        )

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                target, data=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            logger.info(
                "Webhook erfolgreich gesendet: status=%d", response.status_code
            )
            return response
        except requests.RequestException as exc:
            wait = RETRY_BACKOFF ** attempt
            logger.warning(
                "Versuch %d/%d fehlgeschlagen: %s – Warte %ds",
                attempt,
                retries,
                exc,
                wait,
            )
            if attempt < retries:
                time.sleep(wait)

    logger.error("Webhook konnte nach %d Versuchen nicht gesendet werden", retries)
    return None


def main() -> None:
    """Send a test webhook event."""
    data = {"event": "test", "data": "Hallo Welt"}
    send_webhook(data)


if __name__ == "__main__":
    main()

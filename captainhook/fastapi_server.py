"""FastAPI-based webhook server with optional HMAC signature verification."""

import logging
import os
from datetime import datetime, timezone
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from captainhook.security import verify_signature

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CaptainHook", description="Webhook-Empfangsserver")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@app.post("/webhook")
async def webhook(
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
) -> dict[str, str]:
    """Receive and process incoming webhook events."""
    body = await request.body()

    # Signature verification (if a secret is configured)
    if WEBHOOK_SECRET:
        if not x_webhook_signature or not verify_signature(
            body, WEBHOOK_SECRET, x_webhook_signature
        ):
            logger.warning("Invalid signature from %s", request.client.host)
            raise HTTPException(status_code=403, detail="Ungültige Signatur")

    data: dict[str, Any] = await request.json()

    logger.info(
        "Webhook empfangen: event=%s, timestamp=%s",
        data.get("event", "unbekannt"),
        datetime.now(timezone.utc).isoformat(),
    )

    # --- Add your processing logic here ---

    return {"status": "erfolgreich"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health-check endpoint."""
    return {"status": "ok"}


def main() -> None:
    port = int(os.getenv("WEBHOOK_PORT", "5050"))
    logger.info("FastAPI-Webhook-Server startet auf Port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

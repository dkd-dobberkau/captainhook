"""FastAPI-based webhook server with optional HMAC signature verification."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from captainhook.database import add_event, clear_events, get_events, init_db
from captainhook.security import verify_signature

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="CaptainHook",
    description="Webhook-Empfangsserver",
    lifespan=lifespan,
)


@app.post("/webhook")
async def webhook(
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
) -> dict[str, str]:
    """Receive and process incoming webhook events."""
    body = await request.body()

    if WEBHOOK_SECRET:
        if not x_webhook_signature or not verify_signature(
            body, WEBHOOK_SECRET, x_webhook_signature
        ):
            logger.warning("Invalid signature from %s", request.client.host)
            raise HTTPException(status_code=403, detail="Ungültige Signatur")

    data: dict[str, Any] = await request.json()
    now = datetime.now(timezone.utc)
    add_event(data, now.strftime("%H:%M:%S"))

    logger.info(
        "Webhook empfangen: event=%s, timestamp=%s",
        data.get("event", "unbekannt"),
        now.isoformat(),
    )

    return {"status": "erfolgreich"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health-check endpoint."""
    return {"status": "ok"}


@app.get("/events")
async def events(limit: int = 200) -> list[dict]:
    """Return stored webhook events."""
    return get_events(limit=limit)


@app.delete("/events")
async def delete_events() -> dict[str, str]:
    """Delete all stored events."""
    clear_events()
    return {"status": "gelöscht"}


def main() -> None:
    port = int(os.getenv("WEBHOOK_PORT", "5050"))
    logger.info("FastAPI-Webhook-Server startet auf Port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

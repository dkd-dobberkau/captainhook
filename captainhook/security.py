"""HMAC signature verification for webhook security."""

import hashlib
import hmac


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate an HMAC-SHA256 signature for the given payload.

    Args:
        payload: Raw request body as bytes.
        secret: Shared secret key.

    Returns:
        Hex-encoded HMAC-SHA256 signature prefixed with 'sha256='.
    """
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def verify_signature(payload: bytes, secret: str, signature: str) -> bool:
    """Verify an HMAC-SHA256 signature against the expected value.

    Args:
        payload: Raw request body as bytes.
        secret: Shared secret key.
        signature: The signature to verify (with 'sha256=' prefix).

    Returns:
        True if the signature is valid, False otherwise.
    """
    expected = generate_signature(payload, secret)
    return hmac.compare_digest(expected, signature)

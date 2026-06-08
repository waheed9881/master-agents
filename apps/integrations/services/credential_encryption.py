"""Fernet-based credential encryption for channel secrets."""
from __future__ import annotations

from django.conf import settings

PLAIN_PREFIX = "plain:"


def generate_key() -> str:
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()


def _fernet():
    key = getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", "")
    if not key:
        return None
    from cryptography.fernet import Fernet

    return Fernet(key.encode() if isinstance(key, str) else key)


def is_encrypted(value: str) -> bool:
    """True when value is a Fernet ciphertext (not plain: prefixed)."""
    if not value or value.startswith(PLAIN_PREFIX):
        return False
    return value.startswith("gAAAAA") and len(value) > 40


def encrypt_secret(value: str) -> str:
    """Encrypt a secret. Falls back to plain: prefix when key is missing."""
    if not value:
        return ""
    if is_encrypted(value):
        return value
    if value.startswith(PLAIN_PREFIX):
        value = value[len(PLAIN_PREFIX) :]
    fernet = _fernet()
    if not fernet:
        return f"{PLAIN_PREFIX}{value}"
    try:
        return fernet.encrypt(value.encode()).decode()
    except Exception:
        return f"{PLAIN_PREFIX}{value}"


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    if value.startswith(PLAIN_PREFIX):
        return value[len(PLAIN_PREFIX) :]
    fernet = _fernet()
    if not fernet:
        return ""
    try:
        return fernet.decrypt(value.encode()).decode()
    except Exception:
        return ""


def mask_secret(value: str) -> str:
    """Return a safe display string; never exposes raw token."""
    if not value:
        return ""
    if is_encrypted(value):
        return "******** (encrypted)"
    if value.startswith(PLAIN_PREFIX):
        raw = value[len(PLAIN_PREFIX) :]
        if len(raw) <= 4:
            return "**** (plain - not encrypted)"
        return f"****{raw[-4:]} (plain - not encrypted)"
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def rotate_secret_if_plain(value: str) -> str:
    """Re-encrypt plain-prefixed values when encryption key is available."""
    if not value or not value.startswith(PLAIN_PREFIX):
        return value
    if not getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", ""):
        return value
    return encrypt_secret(value[len(PLAIN_PREFIX) :])


def encryption_key_configured() -> bool:
    return bool(getattr(settings, "CREDENTIALS_ENCRYPTION_KEY", ""))


def encryption_status() -> dict:
    """Status summary for security dashboard and audit commands."""
    key_set = encryption_key_configured()
    mock_mode = getattr(settings, "INTEGRATIONS_MOCK_MODE", True)
    if key_set:
        return {"status": "PASS", "message": "Encryption key configured"}
    if mock_mode:
        return {
            "status": "WARN",
            "message": "No encryption key (mock mode - credentials stored as plain:)",
        }
    return {
        "status": "FAIL",
        "message": "CREDENTIALS_ENCRYPTION_KEY required when mock mode is disabled",
    }

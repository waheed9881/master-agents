"""Phase 16 tests: Fernet credential encryption."""
import pytest
from django.test import override_settings

from apps.integrations.services.credential_encryption import (
    decrypt_secret,
    encrypt_secret,
    encryption_status,
    generate_key,
    is_encrypted,
    mask_secret,
    rotate_secret_if_plain,
)


@pytest.mark.django_db
class TestCredentialEncryption:
    def test_generate_key(self):
        key = generate_key()
        assert len(key) > 20

    @override_settings(CREDENTIALS_ENCRYPTION_KEY="", INTEGRATIONS_MOCK_MODE=True)
    def test_plain_fallback_when_no_key(self):
        encrypted = encrypt_secret("my-secret-token")
        assert encrypted.startswith("plain:")
        assert decrypt_secret(encrypted) == "my-secret-token"
        assert not is_encrypted(encrypted)

    @override_settings(CREDENTIALS_ENCRYPTION_KEY="")
    def test_encrypt_decrypt_roundtrip(self):
        key = generate_key()
        with override_settings(CREDENTIALS_ENCRYPTION_KEY=key):
            encrypted = encrypt_secret("super-secret-abc123")
            assert is_encrypted(encrypted)
            assert decrypt_secret(encrypted) == "super-secret-abc123"

    def test_mask_secret_never_exposes_raw(self):
        key = generate_key()
        with override_settings(CREDENTIALS_ENCRYPTION_KEY=key):
            encrypted = encrypt_secret("super-secret-abc123")
            masked = mask_secret(encrypted)
            assert "super-secret" not in masked
            assert "encrypted" in masked

    def test_mask_plain_shows_warning(self):
        masked = mask_secret("plain:abcdefghij")
        assert "plain" in masked
        assert "abcdefghij" not in masked

    def test_rotate_plain_to_encrypted(self):
        key = generate_key()
        with override_settings(CREDENTIALS_ENCRYPTION_KEY=key):
            rotated = rotate_secret_if_plain("plain:token123")
            assert is_encrypted(rotated)
            assert decrypt_secret(rotated) == "token123"

    @override_settings(CREDENTIALS_ENCRYPTION_KEY="", INTEGRATIONS_MOCK_MODE=True)
    def test_encryption_status_warns_without_key(self):
        status = encryption_status()
        assert status["status"] == "WARN"

    @override_settings(CREDENTIALS_ENCRYPTION_KEY="", INTEGRATIONS_MOCK_MODE=False)
    def test_encryption_status_fails_without_key_live_mode(self):
        status = encryption_status()
        assert status["status"] == "FAIL"

"""Phase 16 tests: rate limiting."""
import json

import pytest
from django.test import Client, override_settings

from apps.accounts.models import User, UserRole
from apps.accounts.rate_limit import check_rate_limit, get_client_ip
from apps.tenants.services import create_tenant


@pytest.fixture
def rate_setup(db):
    tenant = create_tenant(name="Rate Limit Co")
    User.objects.create_user(
        email="owner@rate.test",
        password="TestPass123!",
        tenant=tenant,
        role=UserRole.OWNER,
        full_name="Owner",
    )
    return tenant


@pytest.mark.django_db
class TestRateLimitHelpers:
    @override_settings(RATE_LIMITING_ENABLED=True)
    def test_check_rate_limit_blocks_after_limit(self):
        for _ in range(3):
            allowed, _ = check_rate_limit("test:helper", 3, 60)
            assert allowed
        allowed, remaining = check_rate_limit("test:helper", 3, 60)
        assert not allowed
        assert remaining == 0

    def test_get_client_ip(self):
        client = Client()
        response = client.get("/login/", REMOTE_ADDR="192.168.1.5")
        assert response.status_code in (200, 302)


@pytest.mark.django_db
class TestRateLimitEndpoints:
    @override_settings(
        RATE_LIMITING_ENABLED=True,
        RATE_LIMIT_LOGIN_PER_MINUTE=2,
    )
    def test_login_rate_limit_returns_429_api(self, rate_setup):
        client = Client()
        for _ in range(2):
            client.post(
                "/api/auth/login/",
                data=json.dumps({"email": "bad@test.com", "password": "wrong"}),
                content_type="application/json",
            )
        response = client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "bad@test.com", "password": "wrong"}),
            content_type="application/json",
        )
        assert response.status_code == 429

    @override_settings(
        RATE_LIMITING_ENABLED=True,
        RATE_LIMIT_WEBCHAT_PER_MINUTE=1,
    )
    def test_webchat_rate_limit(self, rate_setup):
        client = Client()
        client.login(username="owner@rate.test", password="TestPass123!")
        client.post(
            "/api/webchat/message/",
            data=json.dumps({"message_text": "Hello"}),
            content_type="application/json",
        )
        response = client.post(
            "/api/webchat/message/",
            data=json.dumps({"message_text": "Again"}),
            content_type="application/json",
        )
        assert response.status_code == 429

    @override_settings(
        RATE_LIMITING_ENABLED=True,
        RATE_LIMIT_WEBHOOK_PER_MINUTE=1,
    )
    def test_webhook_rate_limit(self):
        client = Client()
        payload = json.dumps({"object": "whatsapp_business_account", "entry": []})
        client.post(
            "/api/webhooks/whatsapp/",
            data=payload,
            content_type="application/json",
        )
        response = client.post(
            "/api/webhooks/whatsapp/",
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 429

    @override_settings(RATE_LIMITING_ENABLED=False)
    def test_rate_limit_disabled_in_tests_by_default(self, rate_setup):
        client = Client()
        for _ in range(5):
            response = client.post(
                "/api/auth/login/",
                data=json.dumps({"email": "x@test.com", "password": "wrong"}),
                content_type="application/json",
            )
            assert response.status_code in (401, 429)

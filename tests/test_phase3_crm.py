"""Phase 3 tests: CRM module."""
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.crm.models import LeadStatus
from apps.crm.services import (
    create_contact,
    create_lead,
    ensure_default_pipeline_stages,
    score_lead,
    update_lead_score,
)
from apps.tenants.services import create_tenant


@pytest.fixture
def crm_client(client, db):
    tenant = create_tenant(name="CRM Test Co", default_currency="USD")
    User.objects.create_user(
        email="crmtest@example.com",
        password="TestPass123!",
        full_name="CRM Tester",
        tenant=tenant,
        role=UserRole.OWNER,
    )
    client.login(username="crmtest@example.com", password="TestPass123!")
    return client, tenant


@pytest.mark.django_db
class TestPipelineStages:
    def test_create_default_stages(self, crm_client):
        _, tenant = crm_client
        stages = ensure_default_pipeline_stages(tenant)
        assert len(stages) == 7
        assert stages[0].name == "New"
        assert stages[0].is_default is True


@pytest.mark.django_db
class TestContactCreation:
    def test_create_contact(self, crm_client):
        _, tenant = crm_client
        contact = create_contact(
            tenant,
            name="Test User",
            email="test@example.com",
            phone="+1234567890",
        )
        assert contact.pk
        assert contact.tenant == tenant

    def test_api_create_contact(self, crm_client):
        client, _ = crm_client
        response = client.post(
            "/api/contacts/",
            {"name": "API Contact", "email": "api@test.com"},
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "API Contact"


@pytest.mark.django_db
class TestLeadCreation:
    def test_create_lead(self, crm_client):
        _, tenant = crm_client
        contact = create_contact(tenant, name="Lead Contact")
        lead = create_lead(
            tenant,
            contact,
            title="Test Lead",
            status=LeadStatus.QUALIFYING,
            budget="$500",
        )
        update_lead_score(lead)
        assert lead.pk
        assert lead.deals.exists()
        assert lead.score > 0

    def test_lead_scoring(self, crm_client):
        _, tenant = crm_client
        contact = create_contact(
            tenant,
            name="Scored Contact",
            email="scored@test.com",
            phone="+111",
        )
        lead = create_lead(
            tenant,
            contact,
            title="Scored Lead",
            status=LeadStatus.HOT,
            budget="$1000",
            timeline="2 weeks",
            need="Sales automation",
        )
        score = score_lead(lead)
        assert score >= 50

    def test_api_create_lead(self, crm_client):
        client, _ = crm_client
        response = client.post(
            "/api/leads/",
            {
                "contact_name": "New Lead Contact",
                "title": "API Lead",
                "status": "new",
                "budget": "$200",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["title"] == "API Lead"

    def test_api_update_lead(self, crm_client):
        client, tenant = crm_client
        contact = create_contact(tenant, name="Update Contact")
        lead = create_lead(tenant, contact, title="Update Me")
        response = client.patch(
            f"/api/leads/{lead.pk}/",
            {"status": "hot", "budget": "$5000"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "hot"


@pytest.mark.django_db
class TestCRMViews:
    def test_leads_list(self, crm_client):
        client, tenant = crm_client
        contact = create_contact(tenant, name="View Contact")
        create_lead(tenant, contact, title="View Lead")
        response = client.get(reverse("crm:leads"))
        assert response.status_code == 200
        assert b"View Lead" in response.content

    def test_lead_detail(self, crm_client):
        client, tenant = crm_client
        contact = create_contact(tenant, name="Detail Contact", email="detail@test.com")
        lead = create_lead(tenant, contact, title="Detail Lead", status=LeadStatus.HOT)
        response = client.get(reverse("crm:lead_detail", kwargs={"lead_id": lead.pk}))
        assert response.status_code == 200
        assert b"Detail Lead" in response.content

    def test_pipeline_board(self, crm_client):
        client, tenant = crm_client
        ensure_default_pipeline_stages(tenant)
        contact = create_contact(tenant, name="Pipeline Contact")
        create_lead(tenant, contact, title="Pipeline Lead")
        response = client.get(reverse("crm:pipeline"))
        assert response.status_code == 200
        assert b"New" in response.content

    def test_api_pipeline(self, crm_client):
        client, _ = crm_client
        response = client.get("/api/pipeline/")
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data
        assert "board" in data
        assert len(data["stages"]) >= 7

    def test_api_create_task(self, crm_client):
        client, tenant = crm_client
        contact = create_contact(tenant, name="Task Contact")
        lead = create_lead(tenant, contact, title="Task Lead")
        response = client.post(
            "/api/tasks/",
            {"lead_id": lead.pk, "title": "Follow up call"},
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Follow up call"

"""Phase 14 tests: provider fallback, AgentRun tracking, audit compatibility."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import override_settings

from apps.agent_engine.models import AgentRun
from apps.agent_engine.services.orchestrator import AgentOrchestrator
from apps.agent_engine.services.provider_health import complete_with_fallback
from apps.agents.models import AgentTemplate
from apps.agents.services import create_agent_instance
from apps.analytics.selectors import get_agent_engine_counts
from apps.inbox.models import ChannelType
from apps.inbox.services import find_or_create_contact, find_or_create_conversation
from apps.tenants.models import Tenant
from apps.tenants.services import create_tenant


@pytest.mark.django_db
class TestProviderFallback:
    @override_settings(OPENAI_API_KEY="")
    def test_missing_openai_key_falls_back_to_mock(self, db):
        result = complete_with_fallback(
            "You are a sales assistant.",
            "Customer message: Hello",
            provider_name="openai",
        )
        meta = result.metadata or {}
        assert meta.get("fallback_used") is True or meta.get("provider") == "mock"
        assert result.text

    def test_agent_run_records_provider_fields(self, db):
        tenant = create_tenant(name="Run Co")
        template = AgentTemplate.objects.create(
            slug="sales-closing-agent",
            name="Sales",
            description="S",
            category="S",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        contact = find_or_create_contact(tenant, name="Test", source=ChannelType.WEB_CHAT)
        conversation = find_or_create_conversation(
            tenant, contact, channel_type=ChannelType.WEB_CHAT, agent_instance=agent
        )

        orchestrated = AgentOrchestrator.run(agent, conversation, "Hello, I need pricing info")
        assert orchestrated is not None
        run = AgentRun.objects.get(pk=orchestrated.agent_run_id)
        assert run.tokens_used >= 0
        assert run.provider_name
        assert "structured_output" in run.metadata_json

    def test_analytics_includes_token_cost_fallback(self, db):
        tenant = create_tenant(name="Analytics Co")
        template = AgentTemplate.objects.create(
            slug="sales-closing-agent",
            name="Sales",
            description="S",
            category="S",
            is_implemented=True,
        )
        agent = create_agent_instance(tenant, template, status="active")
        contact = find_or_create_contact(tenant, name="A", source=ChannelType.WEB_CHAT)
        conversation = find_or_create_conversation(
            tenant, contact, channel_type=ChannelType.WEB_CHAT, agent_instance=agent
        )
        AgentOrchestrator.run(agent, conversation, "Hi there")

        stats = get_agent_engine_counts(tenant, "all_time")
        assert "total_tokens_used" in stats
        assert "estimated_cost" in stats
        assert "fallback_count" in stats
        assert "runs_by_provider" in stats


@pytest.mark.django_db
class TestAuditMockCompatibility:
    def test_audit_script_uses_mock_by_default(self, db):
        tenant, _ = Tenant.objects.get_or_create(
            slug="demo-company",
            defaults={"name": "Demo Company", "country": "USA"},
        )
        template = AgentTemplate.objects.create(
            slug="sales-closing-agent",
            name="Sales",
            description="S",
            category="S",
            is_implemented=True,
        )
        create_agent_instance(tenant, template, status="active")

        root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env["AUDIT_AI_PROVIDER"] = "mock"
        proc = subprocess.run(
            [sys.executable, str(root / "scripts" / "audit_agent_quality.py")],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
        assert proc.returncode == 0
        assert "Passed:   60" in proc.stdout
        assert "Warnings: 0" in proc.stdout

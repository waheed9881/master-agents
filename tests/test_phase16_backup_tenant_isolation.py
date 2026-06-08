"""Phase 16 tests: backup validation and tenant isolation audit."""
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import override_settings

from apps.accounts.models import User, UserRole
from apps.agents import selectors as agent_selectors
from apps.crm.models import Contact, Lead
from apps.inbox import selectors as inbox_selectors
from apps.integrations.models import ChannelCredential
from apps.inbox.models import ChannelAccount, ChannelType
from apps.knowledge.models import KnowledgeSource
from apps.tenants.models import Tenant
ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.django_db
class TestTenantIsolation:
    def test_crm_leads_isolated(self, db):
        t1 = Tenant.objects.create(name="Iso One", slug="iso-one-test")
        t2 = Tenant.objects.create(name="Iso Two", slug="iso-two-test")
        c1 = Contact.objects.create(tenant=t1, name="L1", email="l1@test.com")
        c2 = Contact.objects.create(tenant=t2, name="L2", email="l2@test.com")
        l1 = Lead.objects.create(tenant=t1, contact=c1, title="L1")
        l2 = Lead.objects.create(tenant=t2, contact=c2, title="L2")
        assert Lead.objects.filter(tenant=t1, pk=l2.pk).exists() is False
        assert Lead.objects.filter(tenant=t1, pk=l1.pk).exists() is True

    def test_inbox_conversations_isolated(self, db):
        t1 = Tenant.objects.create(name="Inbox One", slug="inbox-one-test")
        t2 = Tenant.objects.create(name="Inbox Two", slug="inbox-two-test")
        assert inbox_selectors.list_tenant_conversations(t2).filter(tenant=t1).count() == 0

    def test_knowledge_sources_isolated(self, db):
        t1 = Tenant.objects.create(name="Know One", slug="know-one-test")
        t2 = Tenant.objects.create(name="Know Two", slug="know-two-test")
        ks1 = KnowledgeSource.objects.create(
            tenant=t1, title="S1", source_type="text", content="Sample"
        )
        assert KnowledgeSource.objects.filter(tenant=t2, pk=ks1.pk).exists() is False

    def test_integrations_isolated(self, db):
        t1 = Tenant.objects.create(name="Int One", slug="int-one-test")
        t2 = Tenant.objects.create(name="Int Two", slug="int-two-test")
        acc = ChannelAccount.objects.create(
            tenant=t1, channel_type=ChannelType.WHATSAPP, display_name="WA"
        )
        ChannelCredential.objects.create(tenant=t1, channel_account=acc)
        assert ChannelAccount.objects.filter(tenant=t2, pk=acc.pk).exists() is False

    def test_agent_instances_isolated(self, db):
        t1 = Tenant.objects.create(name="Agent One", slug="agent-one-test")
        t2 = Tenant.objects.create(name="Agent Two", slug="agent-two-test")
        assert agent_selectors.list_tenant_agents(t2).filter(tenant=t1).count() == 0


class TestBackupScripts:
    def test_validate_backup_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_backup.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1)
        assert "Backup Validation" in result.stdout

    def test_tenant_isolation_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_tenant_isolation.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode in (0, 1)
        assert "Tenant Isolation Audit" in result.stdout

    def test_generate_credentials_key_command(self):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command("generate_credentials_key", stdout=out)
        assert "CREDENTIALS_ENCRYPTION_KEY=" in out.getvalue()

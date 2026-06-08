import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("agents", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tenants", "0003_phase16_audit_log"),
    ]

    operations = [
        migrations.CreateModel(
            name="UATSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("demo_version", models.CharField(blank=True, default="MVP 1.7", max_length=64)),
                ("audience", models.CharField(blank=True, default="", max_length=255)),
                ("facilitator", models.CharField(blank=True, default="", max_length=255)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("in_progress", "In Progress"), ("completed", "Completed"), ("signed_off", "Signed Off"), ("blocked", "Blocked")], default="draft", max_length=32)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("signed_off_at", models.DateTimeField(blank=True, null=True)),
                ("summary", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_uat_sessions", to=settings.AUTH_USER_MODEL)),
                ("signed_off_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="signed_off_uat_sessions", to=settings.AUTH_USER_MODEL)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uat_sessions", to="tenants.tenant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UATChecklistItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section", models.CharField(max_length=128)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("expected_result", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("not_tested", "Not Tested"), ("passed", "Passed"), ("failed", "Failed"), ("blocked", "Blocked"), ("skipped", "Skipped")], default="not_tested", max_length=32)),
                ("notes", models.TextField(blank=True, default="")),
                ("order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="checklist_items", to="uat.uatsession")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uat_checklist_items", to="tenants.tenant")),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="FeedbackItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(blank=True, default="uat", max_length=128)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("category", models.CharField(choices=[("bug", "Bug"), ("improvement", "Improvement"), ("feature_request", "Feature Request"), ("UX", "UX"), ("content", "Content"), ("agent_quality", "Agent Quality"), ("security", "Security"), ("production_blocker", "Production Blocker"), ("question", "Question")], default="improvement", max_length=32)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], default="medium", max_length=16)),
                ("status", models.CharField(choices=[("open", "Open"), ("triaged", "Triaged"), ("in_progress", "In Progress"), ("resolved", "Resolved"), ("deferred", "Deferred"), ("rejected", "Rejected")], default="open", max_length=32)),
                ("module_area", models.CharField(blank=True, default="", max_length=64)),
                ("related_url", models.CharField(blank=True, default="", max_length=512)),
                ("screenshot_note", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="feedback_assigned", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="feedback_created", to=settings.AUTH_USER_MODEL)),
                ("related_agent_instance", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="feedback_items", to="agents.agentinstance")),
                ("session", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="feedback_items", to="uat.uatsession")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback_items", to="tenants.tenant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent_engine", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrun",
            name="provider_name",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="agentrun",
            name="model_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="agentrun",
            name="fallback_used",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="agentrun",
            name="metadata_json",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

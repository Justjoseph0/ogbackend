from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="StoredReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("query", models.CharField(max_length=255)),
                ("input_type", models.CharField(max_length=32)),
                ("raw_data", models.JSONField(default=dict)),
                ("report", models.JSONField(default=dict)),
                ("root_hash", models.CharField(blank=True, max_length=132)),
                ("tx_hash", models.CharField(blank=True, max_length=132)),
                ("explorer_url", models.URLField(blank=True)),
                ("storage_status", models.CharField(default="pending", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

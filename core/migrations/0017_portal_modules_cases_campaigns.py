import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_campaigns(apps, schema_editor):
    MarketingCampaign = apps.get_model("core", "MarketingCampaign")
    defaults = [
        ("Facebook Lead Ads", "facebook"),
        ("Google Search", "google"),
        ("WhatsApp Broadcast", "whatsapp"),
    ]
    for name, channel in defaults:
        MarketingCampaign.objects.get_or_create(name=name, channel=channel)


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0001_initial"),
        ("core", "0016_backfill_lead_branch_from_staff"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketingCampaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("channel", models.CharField(
                    choices=[
                        ("facebook", "Facebook"),
                        ("google", "Google Ads"),
                        ("whatsapp", "WhatsApp"),
                        ("other", "Other"),
                    ],
                    default="other",
                    max_length=20,
                )),
                ("budget", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("leads_count", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ClientCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_name", models.CharField(max_length=255)),
                ("service_type", models.CharField(
                    choices=[
                        ("visa", "Visa"),
                        ("admission", "Admission"),
                        ("general", "General Service"),
                    ],
                    default="general",
                    max_length=20,
                )),
                ("status", models.CharField(
                    choices=[
                        ("received", "Received"),
                        ("under_process", "Under Process"),
                        ("submitted", "Submitted"),
                        ("approved", "Approved"),
                        ("completed", "Completed"),
                    ],
                    default="received",
                    max_length=20,
                )),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="assigned_cases",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("branch", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="cases",
                    to="branch.branch",
                )),
                ("lead", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="cases",
                    to="core.lead",
                )),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.RunPython(seed_campaigns, migrations.RunPython.noop),
    ]

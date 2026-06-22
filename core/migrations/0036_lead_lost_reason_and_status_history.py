import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DEFAULT_LOST_REASONS = [
    ("Not interested", "not-interested", 0),
    ("No response / unreachable", "no-response", 1),
    ("Price too high", "price-too-high", 2),
    ("Chose competitor", "chose-competitor", 3),
    ("Wrong contact details", "wrong-contact", 4),
    ("Service not available", "service-unavailable", 5),
    ("Other", "other", 6),
]


def seed_lost_reasons(apps, schema_editor):
    LeadLostReasonType = apps.get_model("core", "LeadLostReasonType")
    for name, code, sort_order in DEFAULT_LOST_REASONS:
        LeadLostReasonType.objects.get_or_create(
            code=code,
            defaults={"name": name, "sort_order": sort_order, "is_active": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0035_lead_staff_status_split"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LeadLostReasonType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("code", models.SlugField(blank=True, max_length=50, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Lost reason",
                "verbose_name_plural": "Lost reasons",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddField(
            model_name="lead",
            name="lost_reason_type",
            field=models.ForeignKey(
                blank=True,
                help_text="Reason type when staff marks the lead as Lost.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leads",
                to="core.leadlostreasontype",
            ),
        ),
        migrations.CreateModel(
            name="LeadStaffStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status_name", models.CharField(blank=True, max_length=255)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lead_staff_status_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="staff_status_history",
                        to="core.lead",
                    ),
                ),
                (
                    "lost_reason_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="status_history_entries",
                        to="core.leadlostreasontype",
                    ),
                ),
                (
                    "to_status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="staff_status_history_entries",
                        to="core.leadstatus",
                    ),
                ),
            ],
            options={
                "verbose_name": "Staff status history",
                "verbose_name_plural": "Staff status history",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(seed_lost_reasons, migrations.RunPython.noop),
    ]

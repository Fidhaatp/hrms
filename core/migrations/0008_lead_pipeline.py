import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0005_branchmanager_is_active"),
        ("core", "0007_alter_leaverequest_leave_category"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("company", models.CharField(blank=True, max_length=255)),
                ("phone", models.CharField(max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("source", models.CharField(blank=True, max_length=100)),
                ("notes", models.TextField(blank=True)),
                (
                    "backoffice_status",
                    models.CharField(
                        choices=[("pending", "Pending check"), ("verified", "Correct lead"), ("rejected", "Not correct")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("backoffice_checked_at", models.DateTimeField(blank=True, null=True)),
                ("backoffice_notes", models.TextField(blank=True)),
                (
                    "followup_status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("contacted", "Contacted"),
                            ("qualified", "Qualified"),
                            ("converted", "Converted"),
                            ("lost", "Lost"),
                        ],
                        default="new",
                        max_length=20,
                    ),
                ),
                (
                    "pipeline_stage",
                    models.CharField(
                        choices=[("submitted", "Submitted"), ("followup", "With follow-up"), ("branch", "With branch")],
                        default="submitted",
                        max_length=20,
                    ),
                ),
                ("next_followup_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "backoffice_checked_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="leads_backoffice_checked",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="leads",
                        to="branch.branch",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="leads_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "followup_assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="leads_followup_assigned",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="LeadRoadmapEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lead_roadmap_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roadmap_entries",
                        to="core.lead",
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]

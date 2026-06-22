from django.db import migrations, models
import django.db.models.deletion


DEFAULT_SOURCES = [
    ("Website", "website"),
    ("Referral", "referral"),
    ("LinkedIn", "linkedin"),
    ("Cold Call", "cold-call"),
    ("Google Ads", "google-ads"),
    ("Trade Show", "trade-show"),
]

DEFAULT_STATUSES = [
    ("Follow up", "new", "active", True, False, 0),
    ("Contacted", "contacted", "active", False, False, 1),
    ("Qualified", "qualified", "pending", False, False, 2),
    ("Converted", "converted", "won", False, True, 3),
    ("Lost", "lost", "closed", False, False, 4),
]


def seed_lead_lookups(apps, schema_editor):
    LeadSource = apps.get_model("core", "LeadSource")
    LeadStatus = apps.get_model("core", "LeadStatus")

    for index, (name, code) in enumerate(DEFAULT_SOURCES):
        LeadSource.objects.get_or_create(
            code=code,
            defaults={"name": name, "sort_order": index, "is_active": True},
        )

    for name, code, badge, is_default, counts_as_converted, sort_order in DEFAULT_STATUSES:
        LeadStatus.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "badge_style": badge,
                "is_default": is_default,
                "counts_as_converted": counts_as_converted,
                "sort_order": sort_order,
                "is_active": True,
            },
        )


def migrate_lead_values(apps, schema_editor):
    Lead = apps.get_model("core", "Lead")
    LeadSource = apps.get_model("core", "LeadSource")
    LeadStatus = apps.get_model("core", "LeadStatus")

    default_status = LeadStatus.objects.get(code="new")
    status_by_code = {row.code: row for row in LeadStatus.objects.all()}
    source_by_name = {row.name.lower(): row for row in LeadSource.objects.all()}

    for lead in Lead.objects.all():
        status_code = lead.followup_status_code or "new"
        lead.followup_status_new_id = status_by_code.get(status_code, default_status).pk

        text = (lead.source_text or "").strip()
        if text:
            source = source_by_name.get(text.lower())
            if not source:
                slug = text.lower().replace(" ", "-")[:50]
                source, _ = LeadSource.objects.get_or_create(
                    code=slug,
                    defaults={"name": text, "is_active": True},
                )
                source_by_name[text.lower()] = source
            lead.source_new_id = source.pk

        lead.save(update_fields=["followup_status_new_id", "source_new_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_lead_staff_conversion_handover"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeadSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("code", models.SlugField(blank=True, max_length=50, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Lead source",
                "verbose_name_plural": "Lead sources",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="LeadStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("code", models.SlugField(blank=True, max_length=50, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "badge_style",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("active", "Active"),
                            ("pending", "Pending"),
                            ("won", "Won"),
                            ("closed", "Closed"),
                        ],
                        default="new",
                        max_length=20,
                    ),
                ),
                ("is_default", models.BooleanField(default=False, help_text="Applied automatically when staff adds a new lead.")),
                ("counts_as_converted", models.BooleanField(default=False, help_text="Include in conversion-rate metrics.")),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Lead status",
                "verbose_name_plural": "Lead statuses",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.RunPython(seed_lead_lookups, migrations.RunPython.noop),
        migrations.RenameField(
            model_name="lead",
            old_name="source",
            new_name="source_text",
        ),
        migrations.RenameField(
            model_name="lead",
            old_name="followup_status",
            new_name="followup_status_code",
        ),
        migrations.AddField(
            model_name="lead",
            name="source_new",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads_migrated",
                to="core.leadsource",
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="followup_status_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads_migrated",
                to="core.leadstatus",
            ),
        ),
        migrations.RunPython(migrate_lead_values, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="lead",
            name="source_text",
        ),
        migrations.RemoveField(
            model_name="lead",
            name="followup_status_code",
        ),
        migrations.RenameField(
            model_name="lead",
            old_name="source_new",
            new_name="source",
        ),
        migrations.RenameField(
            model_name="lead",
            old_name="followup_status_new",
            new_name="followup_status",
        ),
        migrations.AlterField(
            model_name="lead",
            name="followup_status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads",
                to="core.leadstatus",
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads",
                to="core.leadsource",
            ),
        ),
    ]

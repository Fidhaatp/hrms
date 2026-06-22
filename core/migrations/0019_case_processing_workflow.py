from django.conf import settings
from django.db import migrations, models

STATUS_MAP = {
    "received": "opened",
    "under_process": "documents_verified",
    "submitted": "portals_uploaded",
    "approved": "tracking_responses",
    "completed": "completed",
}


def migrate_case_statuses(apps, schema_editor):
    ClientCase = apps.get_model("core", "ClientCase")
    for case in ClientCase.objects.all():
        new_status = STATUS_MAP.get(case.status, case.status)
        if new_status != case.status:
            case.status = new_status
            case.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_clientcase_processing_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="doc_passport_collected",
            field=models.BooleanField(default=False, help_text="Follow-up collected passport copy."),
        ),
        migrations.AddField(
            model_name="lead",
            name="doc_certificates_collected",
            field=models.BooleanField(default=False, help_text="Follow-up collected certificates."),
        ),
        migrations.AddField(
            model_name="lead",
            name="doc_photos_collected",
            field=models.BooleanField(default=False, help_text="Follow-up collected photos."),
        ),
        migrations.AddField(
            model_name="lead",
            name="doc_collection_notes",
            field=models.TextField(blank=True, help_text="Missing documents or collection notes from follow-up."),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="application_reference",
            field=models.CharField(blank=True, help_text="Internal student / application reference.", max_length=120),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="universities_applied",
            field=models.TextField(blank=True, help_text="Universities or programs applied to (one per line)."),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="university_response_summary",
            field=models.TextField(blank=True, help_text="Offers, rejections, or pending responses from universities."),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="customer_status_update",
            field=models.TextField(blank=True, help_text="Latest update communicated to the customer."),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="documents_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="documents_verification_note",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="clientcase",
            name="status",
            field=models.CharField(
                choices=[
                    ("opened", "Case opened"),
                    ("documents_verified", "Documents verified"),
                    ("application_created", "Application created"),
                    ("applied_universities", "Applied to universities"),
                    ("portals_uploaded", "Uploaded to portals"),
                    ("tracking_responses", "Tracking university responses"),
                    ("customer_updated", "Customer status updated"),
                    ("completed", "Case completed"),
                ],
                default="opened",
                max_length=30,
            ),
        ),
        migrations.RunPython(migrate_case_statuses, migrations.RunPython.noop),
        migrations.CreateModel(
            name="CaseProcessingLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage", models.CharField(max_length=30)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="processing_logs",
                        to="core.clientcase",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="case_processing_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

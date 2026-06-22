from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_portal_modules_cases_campaigns"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="clientcase",
            name="submission_reference",
            field=models.CharField(
                blank=True,
                help_text="External reference when submitted to authority/provider.",
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="submitted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="completion_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientcase",
            name="processed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cases_processed",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

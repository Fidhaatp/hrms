from django.db import migrations, models


def backfill_client_type(apps, schema_editor):
    Lead = apps.get_model("core", "Lead")
    individual_values = {"individual", "person", "personal"}
    for lead in Lead.objects.all():
        value = (lead.company or "").strip().lower()
        if value in individual_values:
            lead.company = "individual"
        else:
            lead.company = "company"
        lead.save(update_fields=["company"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0029_lead_phone_email_unique"),
    ]

    operations = [
        migrations.RunPython(backfill_client_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="lead",
            name="company",
            field=models.CharField(
                choices=[("company", "Company"), ("individual", "Individual")],
                default="company",
                max_length=20,
            ),
        ),
    ]

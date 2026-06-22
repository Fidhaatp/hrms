from django.db import migrations


def backfill_staff_converted(apps, schema_editor):
    Lead = apps.get_model("core", "Lead")
    Lead.objects.filter(
        sent_to_followup_at__isnull=False,
        staff_stage="new",
    ).update(staff_stage="converted")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0033_lead_zip_followup_check"),
    ]

    operations = [
        migrations.RunPython(backfill_staff_converted, migrations.RunPython.noop),
    ]

from django.db import migrations


def rename_default_status(apps, schema_editor):
    LeadStatus = apps.get_model("core", "LeadStatus")
    LeadStatus.objects.filter(code="new", name="Follow up").update(name="New")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_alter_leaddocument_uploaded_by"),
    ]

    operations = [
        migrations.RunPython(rename_default_status, migrations.RunPython.noop),
    ]

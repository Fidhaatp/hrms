from django.db import migrations


def set_follow_up_default_status(apps, schema_editor):
    LeadStatus = apps.get_model("core", "LeadStatus")
    LeadStatus.objects.filter(code="new").update(
        name="Follow up",
        badge_style="active",
        is_default=True,
    )
    LeadStatus.objects.exclude(code="new").update(is_default=False)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_dynamic_lead_source_status"),
    ]

    operations = [
        migrations.RunPython(set_follow_up_default_status, migrations.RunPython.noop),
    ]

import django.db.models.deletion
from django.db import migrations, models


def split_staff_and_followup_status(apps, schema_editor):
    Lead = apps.get_model("core", "Lead")
    LeadStatus = apps.get_model("core", "LeadStatus")
    converted = LeadStatus.objects.filter(code="converted").first()
    queue_default = LeadStatus.objects.filter(code="new", is_active=True).first()

    for lead in Lead.objects.all().iterator():
        current_status_id = lead.followup_status_id
        if lead.sent_to_followup_at and converted:
            lead.staff_status_id = converted.pk
        elif current_status_id:
            lead.staff_status_id = current_status_id
        elif queue_default:
            lead.staff_status_id = queue_default.pk

        if not lead.sent_to_followup_at:
            lead.followup_status_id = None
        elif not lead.followup_status_id and queue_default:
            lead.followup_status_id = queue_default.pk

        lead.save(update_fields=["staff_status_id", "followup_status_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0034_backfill_staff_converted_stage"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="staff_status",
            field=models.ForeignKey(
                blank=True,
                help_text="Status set by branch staff on their portal.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads_staff_status",
                to="core.leadstatus",
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="followup_status",
            field=models.ForeignKey(
                blank=True,
                help_text="Status set by the follow-up team (separate from staff status).",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads_followup_status",
                to="core.leadstatus",
            ),
        ),
        migrations.RunPython(split_staff_and_followup_status, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="lead",
            name="staff_status",
            field=models.ForeignKey(
                help_text="Status set by branch staff on their portal.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads_staff_status",
                to="core.leadstatus",
            ),
        ),
    ]

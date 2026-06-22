from django.db import migrations


def backfill_lead_branches(apps, schema_editor):
    Lead = apps.get_model("core", "Lead")
    Staff = apps.get_model("staff", "Staff")

    staff_by_user = {
        row.user_id: row.branch_id
        for row in Staff.objects.filter(branch_id__isnull=False).only("user_id", "branch_id")
    }
    for lead in Lead.objects.filter(branch_id__isnull=True).only("id", "created_by_id", "branch_id"):
        branch_id = staff_by_user.get(lead.created_by_id)
        if branch_id:
            lead.branch_id = branch_id
            lead.save(update_fields=["branch_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_lead_default_status_follow_up"),
        ("staff", "0003_staff_branch"),
    ]

    operations = [
        migrations.RunPython(backfill_lead_branches, migrations.RunPython.noop),
    ]

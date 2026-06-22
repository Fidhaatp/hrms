from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_alter_userprofile_user_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="staff_stage",
            field=models.CharField(
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
        migrations.AddField(
            model_name="lead",
            name="staff_conversion_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="lead",
            name="handover_status",
            field=models.CharField(
                choices=[("pending", "Not handed over"), ("handed_over", "Handed over")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="handover_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="lead",
            name="handed_over_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

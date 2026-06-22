import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0001_initial"),
        ("followup", "0002_followup_profile_refactor"),
    ]

    operations = [
        migrations.AddField(
            model_name="followup",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="followup_members",
                to="branch.branch",
            ),
        ),
    ]

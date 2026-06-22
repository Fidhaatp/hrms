import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0001_initial"),
        ("backoffice", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="backoffice",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="backoffice_members",
                to="branch.branch",
            ),
        ),
    ]

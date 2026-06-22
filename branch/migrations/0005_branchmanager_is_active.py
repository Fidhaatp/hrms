from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0004_alter_branch_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="branchmanager",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="branchmanager",
            name="deactivated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0005_branchmanager_is_active"),
        ("staff", "0002_staff_profile_refactor"),
    ]

    operations = [
        migrations.AddField(
            model_name="staff",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="staff_members",
                to="branch.branch",
            ),
        ),
    ]

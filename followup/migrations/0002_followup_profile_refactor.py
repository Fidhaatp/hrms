import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("followup", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(model_name="followup", name="email"),
        migrations.RemoveField(model_name="followup", name="username"),
        migrations.AddField(
            model_name="followup",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="followup",
            name="deactivated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="followup",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="followup_profile",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="followup",
            name="phone",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterModelOptions(
            name="followup",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Follow-up profile",
                "verbose_name_plural": "Follow-up profiles",
            },
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("staff", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="staff",
            name="email",
        ),
        migrations.RemoveField(
            model_name="staff",
            name="username",
        ),
        migrations.AddField(
            model_name="staff",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="staff",
            name="deactivated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="staff",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="staff_profile",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="staff",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Staff profile",
                "verbose_name_plural": "Staff profiles",
            },
        ),
        migrations.AlterField(
            model_name="staff",
            name="phone",
            field=models.CharField(max_length=20),
        ),
    ]

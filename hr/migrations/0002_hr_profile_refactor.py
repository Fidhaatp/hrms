import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="hr",
            name="email",
        ),
        migrations.RemoveField(
            model_name="hr",
            name="username",
        ),
        migrations.AddField(
            model_name="hr",
            name="department",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="hr",
            name="designation",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="hr",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="hr_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

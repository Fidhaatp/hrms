from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("branch", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="branch",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="branch",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

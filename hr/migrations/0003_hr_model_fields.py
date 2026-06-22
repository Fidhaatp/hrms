from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0002_hr_profile_refactor"),
    ]

    operations = [
        migrations.RenameField(
            model_name="hr",
            old_name="user",
            new_name="username",
        ),
        migrations.RemoveField(
            model_name="hr",
            name="department",
        ),
        migrations.RemoveField(
            model_name="hr",
            name="designation",
        ),
    ]
